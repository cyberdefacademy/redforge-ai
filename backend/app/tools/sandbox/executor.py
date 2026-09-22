import asyncio, hashlib, json, time, os, shutil, re
from pathlib import Path

MAX_STDOUT = 200_000
MAX_STDERR = 50_000

# Executable allowlist: only absolute paths under these prefixes may run.
ALLOWED_EXE_PREFIXES = ("/usr/bin/", "/usr/local/bin/", "/bin/", "/opt/")
ALLOWED_EXE_NAMES = {"nmap", "masscan", "amass", "subfinder", "nuclei", "gobuster", "feroxbuster", "nikto", "whatweb", "hydra", "sqlmap", "echo", "sleep"}
_ENG_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]{0,63}$")


def _sanitize_engagement_id(eid: str) -> str:
    eid = (eid or "global").strip()
    if _ENG_ID_RE.match(eid):
        return eid
    # Hash unsafe values into a safe directory name (prevents ../ traversal).
    return "eng_" + hashlib.sha256(eid.encode()).hexdigest()[:16]


def _sanitized_env() -> dict:
    """Strip secrets from child environment."""
    deny = ("JWT_SECRET", "OPENAI_API_KEY", "OPENROUTER_API_KEY", "GROQ_API_KEY", "TOGETHER_API_KEY",
            "CUSTOM_LLM_API_KEY", "POSTGRES_PASSWORD", "SEED_ADMIN_PASSWORD", "REDIS_PASSWORD",
            "DATABASE_URL", "REDIS_URL", "AWS_SECRET", "GITHUB_TOKEN")
    env = {k: v for k, v in os.environ.items() if k not in deny and not k.endswith("_KEY") and not k.endswith("_SECRET")}
    env["PATH"] = "/usr/bin:/bin:/usr/local/bin"
    return env


def _artifact_dir() -> Path:
    d = Path(os.environ.get("EVIDENCE_DIR", "/var/lib/redforge/evidence"))
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        fallback = Path("/tmp/redforge-evidence")
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback
    return d

ARTIFACT_DIR = _artifact_dir()

class SandboxResult:
    def __init__(self, exit_code, stdout, stderr, duration, artifacts=None):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration = duration
        self.artifacts = artifacts or []

async def execute_sandboxed(cmd: list[str], timeout: int = 300, engagement_id: str = "", tool: str = "", target: str = "", operator: str = "") -> dict:
    """Execute a validated command list with limits. NEVER pass shell=True."""
    start = time.time()
    # Validate: non-empty arg list of plain strings, absolute executable.
    if not cmd:
        return {"exit_code": 1, "stdout": "", "stderr": "Empty command", "duration": 0}
    if not all(isinstance(a, str) and a for a in cmd):
        return {"exit_code": 1, "stdout": "", "stderr": "Invalid command args", "duration": 0}
    exe = cmd[0]
    # Resolve bare executable names via PATH (no shell); reject relative paths with /.
    if "/" not in exe:
        if exe not in ALLOWED_EXE_NAMES:
            return {"exit_code": 1, "stdout": "", "stderr": f"Executable not allowed: {exe}", "duration": 0}
        resolved = shutil.which(exe)
        if not resolved:
            return {"exit_code": 127, "stdout": "", "stderr": f"Executable not found: {exe}", "duration": 0}
        cmd = [resolved, *cmd[1:]]
        exe = resolved
    elif not exe.startswith("/"):
        return {"exit_code": 1, "stdout": "", "stderr": "Executable must be absolute path", "duration": 0}
    # Enforce allowlist on absolute path as well (prevents /bin/rm direct invocation).
    if exe.split("/")[-1] not in ALLOWED_EXE_NAMES or not exe.startswith(ALLOWED_EXE_PREFIXES):
        return {"exit_code": 1, "stdout": "", "stderr": f"Executable not allowed: {exe}", "duration": 0}
    safe_eng = _sanitize_engagement_id(engagement_id)
    timeout = max(1, min(int(timeout or 300), 1800))
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=_sanitized_env(),
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {"exit_code": 124, "stdout": "", "stderr": f"Timeout after {timeout}s", "duration": time.time()-start}
        
        duration = time.time() - start
        stdout_s = stdout.decode(errors="ignore")[:MAX_STDOUT]
        stderr_s = stderr.decode(errors="ignore")[:MAX_STDERR]

        # Provenance
        provenance = {
            "engagement_id": safe_eng,
            "operator": operator,
            "tool": tool,
            "target": target,
            "cmd": cmd,
            "timestamp": time.time(),
            "duration": duration,
            "exit_code": proc.returncode,
        }
        # Hash output for evidence integrity
        sha = hashlib.sha256((stdout_s + stderr_s).encode()).hexdigest()
        provenance["sha256"] = sha

        # Persist artifact for chain-of-custody (best-effort)
        artifact_path = ""
        try:
            base = _artifact_dir()
            sub = base / safe_eng
            sub.mkdir(parents=True, exist_ok=True)
            artifact_path = str(sub / f"{tool}_{int(time.time())}_{sha[:12]}.json")
            with open(artifact_path, "w") as f:
                json.dump({"provenance": provenance, "stdout": stdout_s, "stderr": stderr_s}, f)
        except Exception:
            artifact_path = ""

        return {"exit_code": proc.returncode, "stdout": stdout_s, "stderr": stderr_s, "duration": duration, "provenance": provenance, "sha256": sha, "artifact_path": artifact_path}
    except FileNotFoundError as e:
        return {"exit_code": 127, "stdout": "", "stderr": str(e), "duration": time.time()-start}
    except Exception as e:
        return {"exit_code": 1, "stdout": "", "stderr": str(e), "duration": time.time()-start}
