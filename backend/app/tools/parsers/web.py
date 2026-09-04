import re, json
def parse_gobuster(output: str):
    paths=[]
    for line in output.splitlines():
        m=re.search(r"(\/[^\s]+)\s+\(Status:\s*(\d+)\)", line)
        if m:
            paths.append({"path": m.group(1), "status": int(m.group(2)), "line": line.strip()})
        elif line.strip().startswith("/"):
            paths.append({"path": line.strip().split()[0], "status": 200, "line": line.strip()})
    return paths

def parse_nikto(output: str):
    vulns=[]
    for line in output.splitlines():
        if line.strip().startswith("+") or "OSVDB" in line:
            vulns.append({"title": line.strip().lstrip("+ ").strip()[:300], "severity":"medium", "raw": line.strip()})
    return vulns

def parse_whatweb(output: str):
    tech=[]
    # whatweb: http://x [200 OK] Apache[2.4], JQuery, etc
    for line in output.splitlines():
        m=re.match(r"(\S+)\s+\[(\d+)\s+([^\]]+)\]\s*(.*)", line)
        if m:
            tech.append({"url": m.group(1), "status": int(m.group(2)), "stack": m.group(4)})
    return tech
