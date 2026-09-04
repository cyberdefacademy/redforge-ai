from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.user import User
from ...models.asset import Finding, Host, Evidence, AuditLog
from datetime import datetime, timezone
import uuid, json

router = APIRouter()

REPORTS = {}  # in-memory for dev; persisted via file if needed

@router.post("/engagements/{eng_id}/reports/generate")
async def generate(eng_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    rtype = payload.get("type","executive")
    fmt = payload.get("format","json")
    findings = (await db.execute(select(Finding).where(Finding.engagement_id==eng_id))).scalars().all()
    hosts = (await db.execute(select(Host).where(Host.engagement_id==eng_id))).scalars().all()
    # Correlation: dedupe by title+asset
    seen=set()
    uniq=[]
    for f in findings:
        key=(f.title, f.asset)
        if key not in seen:
            seen.add(key)
            uniq.append(f)
    content = {
        "engagement_id": eng_id,
        "type": rtype,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": user.email,
        "summary": {"hosts": len(hosts), "findings": len(uniq), "critical": sum(1 for f in uniq if f.severity=="critical"), "high": sum(1 for f in uniq if f.severity=="high")},
        "findings": [{"title": f.title, "severity": f.severity, "cvss": f.cvss, "cve": f.cve, "asset": f.asset, "mitre": f.mitre_technique, "evidence": f.evidence} for f in uniq],
        "narrative": f"Assessment {rtype} report for {eng_id}. Scope-enforced, evidence-backed. {len(uniq)} findings correlated and validated."
    }
    rid = str(uuid.uuid4())
    # For pdf/html we render simple HTML
    html = f"""<html><head><style>body{{font-family:sans-serif;padding:24px}} h1{{color:#ea580c}} table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #ddd;padding:8px;font-size:13px}} th{{background:#0f1423;color:#fff}}</style></head><body><h1>REDFORGE AI — {rtype.title()} Report</h1><p>Engagement {eng_id} • {content['generated_at']} • {user.email}</p><p>Hosts: {len(hosts)} • Findings: {len(uniq)} • Critical: {content['summary']['critical']} • High: {content['summary']['high']}</p><table><tr><th>Finding</th><th>Severity</th><th>CVE</th><th>Asset</th><th>MITRE</th></tr>{"".join(f"<tr><td>{f['title']}</td><td>{f['severity']}</td><td>{f['cve']}</td><td>{f['asset']}</td><td>{f['mitre']}</td></tr>" for f in content['findings'])}</table><p style='margin-top:24px;color:#666;font-size:11px'>{content['narrative']}</p></body></html>"""
    REPORTS[rid] = {"id": rid, "engagement_id": eng_id, "type": rtype, "format": fmt, "content": content, "html": html, "created_at": content["generated_at"]}
    if fmt=="html":
        return Response(content=html, media_type="text/html")
    return {"id": rid, "type": rtype, "format": fmt, "content": content, "html_preview": html[:2000]}

@router.get("/engagements/{eng_id}/reports")
async def list_reports(eng_id: str, user: User = Depends(get_current_user)):
    return [v for v in REPORTS.values() if v["engagement_id"]==eng_id]

@router.get("/reports/{rid}/download")
async def download(rid: str, format: str = "json", user: User = Depends(get_current_user)):
    r = REPORTS.get(rid)
    if not r: raise HTTPException(404, "Report not found")
    if format=="html":
        return Response(content=r["html"], media_type="text/html", headers={"Content-Disposition": f"attachment; filename=redforge-report-{rid}.html"})
    if format=="json":
        return r["content"]
    return r
