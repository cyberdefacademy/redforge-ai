from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.user import User
from ...models.engagement import Engagement
from ...models.asset import Task, AuditLog
from datetime import datetime, timezone

router = APIRouter()

@router.get("/engagements/{eng_id}/lab")
async def get_lab(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    eng = (await db.execute(select(Engagement).where(Engagement.id==eng_id))).scalar_one_or_none()
    if not eng: raise HTTPException(404, "Engagement not found")
    # Lab mode is encoded as assessment_type == ctf or a flag in description; we expose it explicitly
    is_lab = eng.assessment_type in ("ctf","lab")
    return {"engagement_id": eng_id, "lab_mode": is_lab, "assessment_type": eng.assessment_type, "status": eng.status}

@router.post("/engagements/{eng_id}/lab")
async def set_lab(eng_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    eng = (await db.execute(select(Engagement).where(Engagement.id==eng_id))).scalar_one_or_none()
    if not eng: raise HTTPException(404, "Not found")
    lab = bool(payload.get("lab_mode"))
    # Map lab_mode to ctf type if true, preserve name
    if lab:
        eng.assessment_type = "ctf"
    else:
        if eng.assessment_type == "ctf":
            eng.assessment_type = "external"
    db.add(AuditLog(engagement_id=eng_id, actor=user.email, action="lab_mode_toggle", target=str(lab), result="success"))
    await db.commit()
    return {"lab_mode": lab, "assessment_type": eng.assessment_type}

@router.get("/engagements/{eng_id}/approvals")
async def list_approvals(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    r = await db.execute(select(Task).where(Task.engagement_id==eng_id, Task.status=="waiting_approval").order_by(Task.created_at.desc()))
    return r.scalars().all()

@router.post("/tasks/{task_id}/approve")
async def approve(task_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in ("administrator","red_team_lead","operator"):
        raise HTTPException(403, "Not allowed")
    t = (await db.execute(select(Task).where(Task.id==task_id))).scalar_one_or_none()
    if not t: raise HTTPException(404, "Task not found")
    t.status = "queued"
    t.risk_level = payload.get("risk_level", t.risk_level)
    db.add(AuditLog(engagement_id=t.engagement_id, actor=user.email, action="approve_task", target=task_id, result="approved"))
    await db.commit()
    return {"status": "approved", "task_id": task_id}

@router.post("/tasks/{task_id}/deny")
async def deny(task_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    t = (await db.execute(select(Task).where(Task.id==task_id))).scalar_one_or_none()
    if not t: raise HTTPException(404, "Not found")
    t.status = "cancelled"
    db.add(AuditLog(engagement_id=t.engagement_id, actor=user.email, action="deny_task", target=task_id, result="denied"))
    await db.commit()
    return {"status": "denied", "task_id": task_id}

@router.get("/engagements/{eng_id}/audit")
async def audit(eng_id: str, limit: int = 100, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    r = await db.execute(select(AuditLog).where(AuditLog.engagement_id==eng_id).order_by(AuditLog.timestamp.desc()).limit(limit))
    return r.scalars().all()

@router.get("/audit")
async def audit_global(limit: int = 100, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    r = await db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit))
    return r.scalars().all()
