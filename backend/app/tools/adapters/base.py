from typing import Dict, Any
import re
import shlex

# Adapter: structured action -> validated CLI

ADAPTERS = {
    "nmap": lambda p: ["/usr/bin/nmap", "-sV", "-Pn"] + (["-p", p["ports"]] if p.get("ports") else []) + [p["target"]],
    "masscan": lambda p: ["/usr/bin/masscan", p["target"]] + (["-p", p["ports"]] if p.get("ports") else ["--top-ports", "100"]) + ["--rate", "1000"],
    "whatweb": lambda p: ["/usr/bin/whatweb", "-a", "3", p["target"]],
    "nuclei": lambda p: ["/usr/bin/nuclei", "-u", p["target"], "-silent"],
    "gobuster": lambda p: ["/usr/bin/gobuster", "dir", "-u", p["target"], "-w", "/usr/share/wordlists/dirb/common.txt", "-q"],
    "feroxbuster": lambda p: ["/usr/bin/feroxbuster", "-u", p["target"], "--silent"],
    "nikto": lambda p: ["/usr/bin/nikto", "-h", p["target"]] + (["-Tuning", p["tuning"]] if p.get("tuning") else []),
    "subfinder": lambda p: ["/usr/bin/subfinder", "-d", p["target"], "-silent"],
    "amass": lambda p: ["/usr/bin/amass", "enum", "-d", p["target"]],
    "hydra": lambda p: ["/usr/bin/hydra", "-t", "4", p["target"], "http-get", "/"],
    "sqlmap": lambda p: ["/usr/bin/sqlmap", "-u", p["target"], "--batch", "--level", "1"],
}

_BLOCKED_CHARS = re.compile(r"[;|&`$(){}[\]!#~*?<>\\'\"@%]")
_BLOCKED_SCHEMES = ("file://", "gopher://", "ftp://", "dict://", "ldap://", "jar:", "javascript:", "data:", "vbscript:")
_MAX_TARGET_LEN = 2048
_MAX_PORTS_LEN = 256


def build_command(tool: str, params: Dict[str, Any]) -> list[str] | None:
    # Fuse validation into build: never build an unvalidated command (prevents TOCTOU bypass).
    ok, _ = validate_params(tool, params)
    if not ok:
        return None
    fn = ADAPTERS.get(tool.lower())
    if not fn:
        return None
    try:
        cmd = fn(params)
        # Validate: no shell injection, all args are strings without dangerous chars
        for arg in cmd:
            if not isinstance(arg, str):
                return None
        return cmd
    except Exception:
        return None

def validate_params(tool: str, params: Dict[str, Any]) -> tuple[bool, str]:
    if tool.lower() not in ADAPTERS:
        return False, f"Unknown tool: {tool}"
    if "target" not in params or not params["target"]:
        return False, "Missing target"
    target = str(params["target"]).strip()
    if len(target) > _MAX_TARGET_LEN:
        return False, "Target too long"
    # Reject control characters / whitespace tricks (newline, CR, tab, null).
    # Targets must never contain whitespace.
    if re.search(r"[\x00-\x20\x7f]", target):
        return False, "Invalid whitespace/control characters"
    is_url = target.startswith("http://") or target.startswith("https://")
    if is_url:
        # URL targets: allow query-string chars (? = & % # . : / - _) but still block shell metachars.
        if re.search(r"[;|`$(){}[\]!~*<>\\'\"@]", target):
            return False, "Invalid target characters"
    else:
        # Bare host/IP/CIDR: strict — no query/shell chars at all.
        if _BLOCKED_CHARS.search(target) or "$(" in target or "`" in target:
            return False, "Invalid target characters"
    lowered = target.lower()
    for scheme in _BLOCKED_SCHEMES:
        if lowered.startswith(scheme):
            return False, "Blocked scheme"
    ports = str(params.get("ports", ""))
    if ports:
        if len(ports) > _MAX_PORTS_LEN or _BLOCKED_CHARS.search(ports):
            return False, "Invalid ports value"
        if not re.fullmatch(r"[0-9,\- ]+", ports):
            return False, "Invalid ports format"
        # Strict port range validation: 1-65535, no empties, no reversed ranges.
        try:
            for part in ports.replace(" ", "").split(","):
                if not part:
                    return False, "Invalid ports format"
                if "-" in part:
                    a, b = part.split("-", 1)
                    ai, bi = int(a), int(b)
                    if not (1 <= ai <= 65535 and 1 <= bi <= 65535 and ai <= bi):
                        return False, "Port out of range (1-65535)"
                else:
                    pi = int(part)
                    if not 1 <= pi <= 65535:
                        return False, "Port out of range (1-65535)"
        except ValueError:
            return False, "Invalid ports format"
    # Nikto scan tuning: only Nikto's own category codes (prevents option injection).
    tuning = str(params.get("tuning", ""))
    if tuning:
        if tool.lower() != "nikto":
            return False, "tuning is only supported for nikto"
        if len(tuning) > 8 or not re.fullmatch(r"[0-9a-dx]+", tuning):
            return False, "Invalid tuning value (nikto codes 0-9 a-d x)"
    return True, "OK"
