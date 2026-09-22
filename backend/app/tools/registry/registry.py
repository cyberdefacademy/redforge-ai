import yaml, pathlib, os, shutil

REGISTRY_DIR = pathlib.Path(__file__).parent

DEFAULT_TOOLS = [
    {"name":"nmap","executable":"/usr/bin/nmap","category":"reconnaissance","risk_level":"low","timeout":300,"requires_approval":False},
    {"name":"masscan","executable":"/usr/bin/masscan","category":"reconnaissance","risk_level":"medium","timeout":600,"requires_approval":False},
    {"name":"amass","executable":"/usr/bin/amass","category":"reconnaissance","risk_level":"low","timeout":600,"requires_approval":False},
    {"name":"subfinder","executable":"/usr/bin/subfinder","category":"reconnaissance","risk_level":"low","timeout":300,"requires_approval":False},
    {"name":"nuclei","executable":"/usr/bin/nuclei","category":"vulnerability","risk_level":"medium","timeout":600,"requires_approval":True},
    {"name":"gobuster","executable":"/usr/bin/gobuster","category":"web","risk_level":"medium","timeout":300,"requires_approval":True},
    {"name":"feroxbuster","executable":"/usr/bin/feroxbuster","category":"web","risk_level":"medium","timeout":600,"requires_approval":True},
    {"name":"nikto","executable":"/usr/bin/nikto","category":"web","risk_level":"medium","timeout":600,"requires_approval":True},
    {"name":"whatweb","executable":"/usr/bin/whatweb","category":"reconnaissance","risk_level":"low","timeout":120,"requires_approval":False},
    {"name":"hydra","executable":"/usr/bin/hydra","category":"password_auditing","risk_level":"high","timeout":900,"requires_approval":True},
    {"name":"sqlmap","executable":"/usr/bin/sqlmap","category":"web","risk_level":"high","timeout":900,"requires_approval":True},
]

def load_registry():
    tools = []
    for t in DEFAULT_TOOLS:
        # Check if binary exists, set status (no shell)
        exists = os.path.exists(t["executable"]) or shutil.which(t["name"]) is not None
        t = {**t, "status": "ready" if exists else "not_installed", "installed": exists}
        tools.append(t)
    return tools

def get_tool(name: str):
    for t in load_registry():
        if t["name"] == name:
            return t
    return None
