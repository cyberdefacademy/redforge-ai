from enum import Enum

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Risk assignment per tool category / action.
# NOTE: high-request-volume scanners are medium (approval-gated) even though
# they are "read-only": a full nikto/nuclei/dir-bust run sends thousands of
# requests and has been observed crashing fragile apps (DoS by volume).
RISK_MAP = {
    "nmap": "low",
    "masscan": "medium",
    "amass": "low",
    "subfinder": "low",
    "nuclei": "medium",
    "gobuster": "medium",
    "feroxbuster": "medium",
    "nikto": "medium",
    "whatweb": "low",
    "hydra": "high",
    "sqlmap": "high",
    "burp": "medium",
    "zap": "medium",
}

APPROVAL_REQUIRED = {"medium": True, "high": True, "critical": True, "low": False}

def evaluate_risk(tool: str, target: str = "", mode: str = "enumeration") -> dict:
    base = RISK_MAP.get(tool.lower(), "high")
    # Unknown tools fail-closed to high (require approval).
    # Escalate if intrusive mode
    if mode in ("intrusive","exploit","bruteforce"):
        if base == "low": base = "medium"
        elif base == "medium": base = "high"
    return {
        "risk": base,
        "requires_approval": APPROVAL_REQUIRED[base],
        "reason": f"Tool {tool} base risk {base}, mode {mode}"
    }
