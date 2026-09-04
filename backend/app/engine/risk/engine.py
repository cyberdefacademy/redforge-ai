from enum import Enum

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Risk assignment per tool category / action
RISK_MAP = {
    "nmap": "low",
    "masscan": "medium",
    "amass": "low",
    "subfinder": "low",
    "nuclei": "low",
    "gobuster": "low",
    "feroxbuster": "low",
    "nikto": "low",
    "whatweb": "low",
    "hydra": "high",
    "sqlmap": "high",
    "burp": "medium",
    "zap": "medium",
}

APPROVAL_REQUIRED = {"medium": False, "high": True, "critical": True, "low": False}

def evaluate_risk(tool: str, target: str = "", mode: str = "enumeration") -> dict:
    base = RISK_MAP.get(tool.lower(), "medium")
    # Escalate if intrusive mode
    if mode in ("intrusive","exploit","bruteforce"):
        if base == "low": base = "medium"
        elif base == "medium": base = "high"
    return {
        "risk": base,
        "requires_approval": APPROVAL_REQUIRED[base],
        "reason": f"Tool {tool} base risk {base}, mode {mode}"
    }
