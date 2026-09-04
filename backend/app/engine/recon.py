from ..tools.parsers.nmap import parse_nmap_text, parse_nuclei
from ..tools.parsers.web import parse_gobuster, parse_nikto, parse_whatweb

def normalize_evidence(tool: str, stdout: str):
    if tool=="nmap": return {"ports": parse_nmap_text(stdout)}
    if tool=="nuclei": return {"findings": parse_nuclei(stdout)}
    if tool=="gobuster": return {"paths": parse_gobuster(stdout)}
    if tool=="nikto": return {"vulns": parse_nikto(stdout)}
    if tool=="whatweb": return {"tech": parse_whatweb(stdout)}
    return {"raw": stdout[:5000]}
