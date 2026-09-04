from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.user import User
from ...models.asset import Host, Service, Finding, Evidence, AuditLog
import json, uuid, hashlib

router = APIRouter()

# AD
@router.post("/engagements/{eng_id}/ad/enumerate")
async def ad_enumerate(eng_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    domain = payload.get("domain","corp.local")
    # Stub: creates findings representing AD misconfigs; in production крови BLOODHOUND ingestion
    findings=[]
    for title, sev, mitre in [("Weak Password Policy","medium","T1110"),("Kerberoastable Accounts","high","T1558.003"),("Unconstrained Delegation","high","T1548"),("DCSync Permissions","critical","T1003.006")]:
        f=Finding(engagement_id=eng_id, title=f"AD: {title} ({domain})", severity=sev, asset=domain, confidence="suspected", mitre_technique=mitre)
        db.add(f); findings.append(title)
    await db.commit()
    db.add(AuditLog(engagement_id=eng_id, actor=user.email, action="ad_enumerate", target=domain, result="success"))
    await db.commit()
    return {"domain": domain, "findings_queued": findings}

@router.get("/engagements/{eng_id}/ad/graph")
async def ad_graph(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    # Returns privilege graph stub compatible with AttackGraph React Flow
    hosts = (await db.execute(select(Host).where(Host.engagement_id==eng_id))).scalars().all()
    nodes=[{"id":"domain","type":"domain","data":{"label":"Domain"},"position":{"x":200,"y":0}}]
    edges=[]
    for i,h in enumerate(hosts[:6]):
        nid=h.id
        nodes.append({"id": nid, "type":"host","data":{"label":h.ip},"position":{"x": i*180, "y": 120}})
        edges.append({"id": f"domain-{nid}", "source":"domain","target":nid, "label":"member"})
    return {"nodes": nodes, "edges": edges}

# Cloud
@router.post("/engagements/{eng_id}/cloud/scan")
async def cloud_scan(eng_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    provider = payload.get("provider","aws")
    scope = payload.get("scope","account")
    checks=[("Public S3 Bucket","high","T1580"),("Overly Permissive IAM","critical","T1078.004"),("Exposed Security Group (0.0.0.0/0)","high","T1046")]
    for title, sev, mitre in checks:
        db.add(Finding(engagement_id=eng_id, title=f"Cloud({provider}): {title}", severity=sev, asset=scope, confidence="detected", mitre_technique=mitre))
    await db.commit()
    return {"provider": provider, "scope": scope, "checks": len(checks)}

@router.get("/engagements/{eng_id}/cloud/posture")
async def cloud_posture(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    findings=(await db.execute(select(Finding).where(Finding.engagement_id==eng_id))).scalars().all()
    cloud=[f for f in findings if f.title.startswith("Cloud")]
    by_sev={}
    for f in cloud: by_sev[f.severity]=by_sev.get(f.severity,0)+1
    return {"cloud_findings": len(cloud), "by_severity": by_sev, "items": [{"title":f.title,"severity":f.severity,"asset":f.asset} for f in cloud]}

# Wireless
@router.post("/engagements/{eng_id}/wireless/scan")
async def wireless_scan(eng_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    ssid=payload.get("ssid","LAB-WIFI")
    findings=[("Weak WPA2-PSK","medium"),("WPS Enabled","high")]
    for t,sev in findings:
        db.add(Finding(engagement_id=eng_id, title=f"Wireless: {t} ({ssid})", severity=sev, asset=ssid, confidence="suspected"))
    await db.commit()
    return {"ssid": ssid, "findings": len(findings)}

# Web deep
@router.post("/engagements/{eng_id}/web/assess")
async def web_assess(eng_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    url=payload.get("url","")
    if not url: raise HTTPException(400, "url required")
    # Stub: import nuclei findings if provided
    for f in payload.get("findings", []):
        db.add(Finding(engagement_id=eng_id, title=f.get("name","Web finding")[:500], severity=f.get("severity","medium"), asset=url, cve=f.get("cve",""), mitre_technique=f.get("mitre","T1190"), confidence="detected"))
    await db.commit()
    return {"url": url, "queued": len(payload.get("findings",[]))}

# Purple-team
@router.post("/engagements/{eng_id}/purple/exercise")
async def purple_exercise(eng_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    technique=payload.get("technique","T1595")
    detected=payload.get("detected", False)
    f=Finding(engagement_id=eng_id, title=f"Purple: {technique} — {'DETECTED' if detected else 'UNDETECTED'}", severity="medium", asset=payload.get("asset",""), mitre_technique=technique, confidence="validated" if detected else "suspected")
    db.add(f)
    db.add(AuditLog(engagement_id=eng_id, actor=user.email, action="purple_exercise", target=technique, result="detected" if detected else "undetected"))
    await db.commit()
    return {"technique": technique, "detected": detected, "finding_id": f.id}

@router.get("/engagements/{eng_id}/purple/coverage")
async def purple_coverage(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    findings=(await db.execute(select(Finding).where(Finding.engagement_id==eng_id))).scalars().all()
    mitre=set(f.mitre_technique for f in findings if f.mitre_technique)
    return {"techniques_covered": sorted(list(mitre)), "count": len(mitre)}
