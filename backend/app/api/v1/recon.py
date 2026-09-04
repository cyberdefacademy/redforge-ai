from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.user import User
from ...models.asset import Host, Port, Service, Finding, Evidence, AuditLog
from ...engine.recon import normalize_evidence
import re, json, hashlib, uuid

router = APIRouter()

def parse_nmap(output: str):
    hosts=[]
    for m in re.finditer(r"(\d+)/tcp\s+open\s+(\S+)", output):
        hosts.append({"port": int(m.group(1)), "service": m.group(2)})
    return hosts

@router.get("/engagements/{eng_id}/assets")
async def asset_inventory(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    hosts = (await db.execute(select(Host).where(Host.engagement_id==eng_id))).scalars().all()
    result=[]
    for h in hosts:
        ports = (await db.execute(select(Port).where(Port.host_id==h.id))).scalars().all()
        port_list=[]
        for p in ports:
            svc = (await db.execute(select(Service).where(Service.port_id==p.id))).scalars().all()
            port_list.append({"id": p.id, "port": p.port, "protocol": p.protocol, "state": p.state, "services": [{"name": s.name, "version": s.version, "banner": s.banner} for s in svc]})
        result.append({"id": h.id, "ip": h.ip, "hostname": h.hostname, "os": h.os, "status": h.status, "ports": port_list})
    return result

@router.post("/engagements/{eng_id}/recon/ingest")
async def recon_ingest(eng_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Ingest raw tool output → normalized assets + findings + evidence (Phase 4)."""
    tool = payload.get("tool","nmap")
    stdout = payload.get("stdout","")
    target = payload.get("target","")
    if not stdout: raise HTTPException(400, "stdout required")
    norm = normalize_evidence(tool, stdout)
    created=[]
    # evidence hash
    sha = hashlib.sha256(stdout.encode()).hexdigest()
    ev = Evidence(engagement_id=eng_id, task_id=payload.get("task_id"), type=f"{tool}_output", file_path=f"ingest:{tool}:{sha[:8]}", sha256=sha, metadata_json=json.dumps({"tool":tool,"target":target, "normalized": norm}) )
    db.add(ev)
    # create hosts/ports/findings
    if "ports" in norm and target:
        host = Host(engagement_id=eng_id, ip=target, hostname=payload.get("hostname",""), os="", status="discovered")
        db.add(host); await db.flush()
        for pr in norm["ports"]:
            p = Port(host_id=host.id, port=pr["port"], protocol=pr.get("protocol","tcp"), state=pr.get("state","open"))
            db.add(p); await db.flush()
            if pr.get("service"):
                db.add(Service(port_id=p.id, name=pr["service"], version=pr.get("version",""), banner=""))
        created.append({"host": host.ip, "ports": len(norm["ports"])})
    for f in norm.get("findings", []):
        db.add(Finding(engagement_id=eng_id, title=f.get("title","finding")[:500], severity=f.get("severity","medium"), asset=f.get("asset", target), confidence="detected"))
        created.append({"finding": f.get("title")})
    for p in norm.get("paths", []):
        db.add(Finding(engagement_id=eng_id, title=f"Path {p['path']}", severity="info", asset=target, confidence="detected"))
    for v in norm.get("vulns", []):
        db.add(Finding(engagement_id=eng_id, title=v["title"][:500], severity=v.get("severity","medium"), asset=target, confidence="detected"))
    await db.commit()
    return {"normalized": norm, "evidence_sha256": sha, "created": created}

@router.post("/engagements/{eng_id}/recon/scan")
async def recon_scan(eng_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    target = payload.get("target","")
    nmap_output = payload.get("nmap_output","")
    if not target: raise HTTPException(400, "target required")
    host = Host(engagement_id=eng_id, ip=target, hostname=payload.get("hostname",""), os=payload.get("os",""), status="discovered")
    db.add(host); await db.flush()
    ports=[]
    if nmap_output:
        parsed = parse_nmap(nmap_output)
        for pr in parsed:
            p = Port(host_id=host.id, port=pr["port"], protocol="tcp", state="open")
            db.add(p); await db.flush()
            s = Service(port_id=p.id, name=pr["service"], version="", banner="")
            db.add(s); ports.append(pr)
    await db.commit()
    await db.refresh(host)
    return {"host": {"id": host.id, "ip": host.ip}, "ports_discovered": ports}

@router.get("/engagements/{eng_id}/recon/summary")
async def recon_summary(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    hosts = (await db.execute(select(Host).where(Host.engagement_id==eng_id))).scalars().all()
    ports = []
    for h in hosts:
        pr = (await db.execute(select(Port).where(Port.host_id==h.id))).scalars().all()
        ports.extend(pr)
    findings = (await db.execute(select(Finding).where(Finding.engagement_id==eng_id))).scalars().all()
    return {"hosts": len(hosts), "ports": len(ports), "findings": len(findings)}
