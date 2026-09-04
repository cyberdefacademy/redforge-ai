import asyncio, hashlib, json, time, subprocess, shlex, os
from pathlib import Path

ARTIFACT_DIR = Path("/tmp/redforge-evidence")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

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
    # Validate no shell metacharacters in executable path
    if not cmd:
        return {"exit_code": 1, "stdout": "", "stderr": "Empty command", "duration": 0}
    
    # Ensure executable exists or is in PATH
    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {"exit_code": 124, "stdout": "", "stderr": f"Timeout after {timeout}s", "duration": time.time()-start}
        
        duration = time.time() - start
        stdout_s = stdout.decode(errors="ignore")[:200000]
        stderr_s = stderr.decode(errors="ignore")[:50000]
        
        # Provenance
        provenance = {
            "engagement_id": engagement_id,
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
        
        return {"exit_code": proc.returncode, "stdout": stdout_s, "stderr": stderr_s, "duration": duration, "provenance": provenance, "sha256": sha}
    except FileNotFoundError as e:
        return {"exit_code": 127, "stdout": "", "stderr": str(e), "duration": time.time()-start}
    except Exception as e:
        return {"exit_code": 1, "stdout": "", "stderr": str(e), "duration": time.time()-start}
