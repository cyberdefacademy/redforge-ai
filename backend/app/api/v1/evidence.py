from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.user import User
from ...models.asset import Evidence, AuditLog
import hashlib, uuid, pathlib, json
from datetime import datetime, timezone

router = APIRouter()
STORE = pathlib.Path("/tmp/redforge-evidence")
STORE.mkdir(parents=True, exist_ok=True)

@router.get("/engagements/{eng_id}/evidence")
async def list_evidence(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    r = await db.execute(select(Evidence).where(Evidence.engagement_id==eng_id).order_by(Evidence.created_at.desc()))
    return r.scalars().all()

@router.post("/engagements/{eng_id}/evidence")
async def upload_evidence(eng_id: str, file: UploadFile = File(...), tool: str = "", description: str = "", db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    data = await file.read()
    sha = hashlib.sha256(data).hexdigest()
    fid = str(uuid.uuid4())
    ext = pathlib.Path(file.filename or "artifact.bin").suffix
    dest = STORE / f"{fid}{ext}"
    dest.write_bytes(data)
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
    return ev

@router.delete("/evidence/{ev_id}")
async def delete_evidence(ev_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in ("administrator","red_team_lead"):
        raise HTTPException(403, "Only lead/admin can delete evidence")
    r = await db.execute(select(Evidence).where(Evidence.id==ev_id))
    ev = r.scalar_one_or_none()
    if not ev: raise HTTPException(404, "Not found")
    await db.delete(ev)
    await db.commit()
    return {"deleted": ev_id}
