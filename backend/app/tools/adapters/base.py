from typing import Dict, Any
import shlex

# Adapter: structured action -> validated CLI

ADAPTERS = {
    "nmap": lambda p: ["/usr/bin/nmap", "-sV", "-Pn"] + (["-p", p["ports"]] if p.get("ports") else []) + [p["target"]],
    "whatweb": lambda p: ["/usr/bin/whatweb", "-a", "3", p["target"]],
    "nuclei": lambda p: ["/usr/bin/nuclei", "-u", p["target"], "-silent"],
    "gobuster": lambda p: ["/usr/bin/gobuster", "dir", "-u", p["target"], "-w", "/usr/share/wordlists/dirb/common.txt", "-q"],
    "nikto": lambda p: ["/usr/bin/nikto", "-h", p["target"]],
    "subfinder": lambda p: ["/usr/bin/subfinder", "-d", p["target"], "-silent"],
    "amass": lambda p: ["/usr/bin/amass", "enum", "-d", p["target"]],
}

def build_command(tool: str, params: Dict[str, Any]) -> list[str] | None:
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
    if "target" not in params or not params["target"]:
        return False, "Missing target"
    # Basic SSRF / injection checks
    target = params["target"]
    if ";" in target or "|" in target or "`" in target or "$(" in target:
        return False, "Invalid target characters"
    if target.startswith("file://") or target.startswith("gopher://"):
        return False, "Blocked scheme"
    return True, "OK"
