from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.deps import get_current_user
from ...core.config import settings
from ...models.user import User
from ...models.asset import Evidence, AuditLog
import hashlib, uuid, pathlib, json, os
from datetime import datetime, timezone

router = APIRouter()
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED_EXTS = {".txt", ".json", ".xml", ".html", ".md", ".csv", ".log", ".pcap", ".png", ".jpg", ".jpeg", ".pdf", ".bin"}

def _store() -> pathlib.Path:
    d = pathlib.Path(os.environ.get("EVIDENCE_DIR", settings.EVIDENCE_DIR))
    d.mkdir(parents=True, exist_ok=True)
    return d

@router.get("/engagements/{eng_id}/evidence")
async def list_evidence(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    r = await db.execute(select(Evidence).where(Evidence.engagement_id==eng_id).order_by(Evidence.created_at.desc()))
    return r.scalars().all()

@router.post("/engagements/{eng_id}/evidence")
async def upload_evidence(eng_id: str, file: UploadFile = File(...), tool: str = "", description: str = "", db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 25MB)")
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    sha = hashlib.sha256(data).hexdigest()
    fid = str(uuid.uuid4())
    ext = pathlib.Path(file.filename or "artifact.bin").suffix.lower()[:10] or ".bin"
    if ext not in ALLOWED_EXTS:
        ext = ".bin"
    dest = _store() / f"{fid}{ext}"
    dest.write_bytes(data)
    try:
        dest.chmod(0o640)
    except Exception:
        pass
    ev = Evidence(id=fid, engagement_id=eng_id, task_id=None, type=file.content_type or "artifact", file_path=str(dest), sha256=sha, metadata_json=json.dumps({"filename": file.filename, "tool": tool, "description": description, "uploader": user.email, "size": len(data)}))
    db.add(ev)
    db.add(AuditLog(engagement_id=eng_id, actor=user.email, action="evidence_upload", target=file.filename or fid, result="success", metadata_json=json.dumps({"sha256": sha})))
    await db.commit()
    await db.refresh(ev)
    return ev

@router.get("/evidence/{ev_id}")
async def get_evidence(ev_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    r = await db.execute(select(Evidence).where(Evidence.id==ev_id))
    ev = r.scalar_one_or_none()
    if not ev: raise HTTPException(404, "Evidence not found")
    # Re-hash file on read: tamper-evident verification.
    try:
        raw = pathlib.Path(ev.file_path).read_bytes()
        current = hashlib.sha256(raw).hexdigest()
        if current != ev.sha256:
            db.add(AuditLog(engagement_id=ev.engagement_id, actor=user.email, action="evidence_integrity_mismatch", target=ev_id, result="alert", metadata_json=json.dumps({"expected": ev.sha256, "actual": current})))
            await db.commit()
            raise HTTPException(status_code=409, detail="Evidence integrity mismatch — file modified")
    except HTTPException:
        raise
    except Exception:
        pass
    return ev

@router.delete("/evidence/{ev_id}")
async def delete_evidence(ev_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in ("administrator","red_team_lead"):
        raise HTTPException(403, "Only lead/admin can delete evidence")
    r = await db.execute(select(Evidence).where(Evidence.id==ev_id))
    ev = r.scalar_one_or_none()
    if not ev: raise HTTPException(404, "Not found")
    fpath = ev.file_path
    await db.delete(ev)
    db.add(AuditLog(engagement_id=ev.engagement_id, actor=user.email, action="evidence_delete", target=ev_id, result="success"))
    await db.commit()
    # Remove orphaned file (best-effort).
    try:
        if fpath:
            pathlib.Path(fpath).unlink(missing_ok=True)
    except Exception:
        pass
    return {"deleted": ev_id}
