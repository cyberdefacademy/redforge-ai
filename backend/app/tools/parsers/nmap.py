import re, xml.etree.ElementTree as ET
def parse_nmap_text(output: str):
    ports=[]
    for m in re.finditer(r"(\d+)/tcp\s+(open|filtered)\s*(\S*)", output):
        ports.append({"port": int(m.group(1)), "protocol":"tcp","state": m.group(2), "service": m.group(3)})
    for m in re.finditer(r"(\d+)/udp\s+(open|filtered)\s*(\S*)", output):
        ports.append({"port": int(m.group(1)), "protocol":"udp","state": m.group(2), "service": m.group(3)})
    return ports

def parse_nmap_xml(xml_text: str):
    try:
        root=ET.fromstring(xml_text)
        out=[]
        for host in root.findall("host"):
            addr=host.find("address")
            ip=addr.get("addr") if addr is not None else ""
            for p in host.findall("ports/port"):
                state=p.find("state")
                service=p.find("service")
                out.append({"ip": ip, "port": int(p.get("portid")), "protocol": p.get("protocol"), "state": state.get("state") if state is not None else "open", "service": service.get("name") if service is not None else "", "version": service.get("version") if service is not None else ""})
        return out
    except Exception:
        return parse_nmap_text(xml_text)

def parse_nuclei(output: str):
    findings=[]
    for line in output.splitlines():
        # nuclei: [high] template - target
        m=re.match(r"\[(\w+)\]\s+(\S+)\s+\(?(.*)\)?", line)
        if m:
            findings.append({"severity": m.group(1).lower(), "title": m.group(2), "asset": m.group(3) or line})
        elif line.strip():
            findings.append({"severity":"info","title": line.strip()[:200], "asset":""})
    return findings
