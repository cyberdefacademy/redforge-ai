from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.user import User
from ...models.engagement import Engagement
from ...models.scope import ScopeTarget, ScopeExclusion, Authorization
from ...models.asset import AuditLog
from ...schemas.engagement import EngagementCreate, EngagementOut, ScopeTargetIn, ScopeExclusionIn
from ...engine.scope.guard import ScopeGuard
from ...engine.mission.controller import activate_kill_switch, clear_kill_switch, is_killed
import uuid

router = APIRouter()

def _audit(db, engagement_id, actor, action, target=""):
    db.add(AuditLog(engagement_id=engagement_id, actor=actor, action=action, target=target, result="success"))

@router.get("", response_model=list[EngagementOut])
async def list_engagements(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Engagement).order_by(Engagement.created_at.desc()))
    return result.scalars().all()

@router.post("", response_model=EngagementOut)
async def create_engagement(payload: EngagementCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    eng = Engagement(name=payload.name, customer=payload.customer, description=payload.description, operator_id=user.id, assessment_type=payload.assessment_type, start_date=payload.start_date, end_date=payload.end_date)
    db.add(eng)
    await db.commit()
    await db.refresh(eng)
    # auto-create authorization stub
    db.add(Authorization(engagement_id=eng.id))
    await db.commit()
    _audit(db, eng.id, user.email, "create_engagement", eng.name)
    await db.commit()
    return eng

@router.get("/{eng_id}", response_model=EngagementOut)
async def get_engagement(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Engagement).where(Engagement.id == eng_id))
    eng = result.scalar_one_or_none()
    if not eng:
        raise HTTPException(status_code=404, detail="Engagement not found")
    return eng

@router.put("/{eng_id}", response_model=EngagementOut)
async def update_engagement(eng_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in ("administrator", "red_team_lead"):
        raise HTTPException(status_code=403, detail="Only lead/admin can update engagements")
    result = await db.execute(select(Engagement).where(Engagement.id == eng_id))
    eng = result.scalar_one_or_none()
    if not eng:
        raise HTTPException(status_code=404, detail="Not found")
    # Allowlist mutable fields (prevents operator_id/status privilege escalation via mass-assignment).
    for k in ("name", "customer", "description", "assessment_type", "start_date", "end_date"):
        v = payload.get(k)
        if v is not None:
            setattr(eng, k, v)
    await db.commit()
    await db.refresh(eng)
    return eng

@router.post("/{eng_id}/authorize")
async def authorize(eng_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in ("administrator","red_team_lead"):
        raise HTTPException(status_code=403, detail="Only lead/admin can authorize engagements")
    result = await db.execute(select(Authorization).where(Authorization.engagement_id == eng_id))
    auth = result.scalar_one_or_none()
    if not auth:
        auth = Authorization(engagement_id=eng_id)
        db.add(auth)
    auth.confirmed = True
    auth.confirmed_by = user.id
    from datetime import datetime, timezone
    auth.confirmed_at = datetime.now(timezone.utc)
    if payload.get("emergency_contact"):
        auth.emergency_contact = payload["emergency_contact"]
    if payload.get("scope_summary"):
        auth.scope_summary = payload["scope_summary"]
    # Update engagement status
    eng = (await db.execute(select(Engagement).where(Engagement.id == eng_id))).scalar_one_or_none()
    if eng:
        eng.status = "authorized"
    await db.commit()
    _audit(db, eng_id, user.email, "authorize_engagement")
    await db.commit()
    return {"status": "authorized", "engagement_id": eng_id}

@router.post("/{eng_id}/kill")
async def kill(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in ("administrator", "red_team_lead", "operator"):
        raise HTTPException(status_code=403, detail="Not allowed")
    activate_kill_switch(eng_id, reason=f"Triggered by {user.email}")
    _audit(db, eng_id, user.email, "emergency_stop")
    await db.commit()
    return {"status": "killed", "engagement_id": eng_id}

@router.post("/{eng_id}/resume")
async def resume(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in ("administrator","red_team_lead"):
        raise HTTPException(status_code=403, detail="Only lead/admin can resume")
    clear_kill_switch(eng_id)
    _audit(db, eng_id, user.email, "resume_engagement")
    await db.commit()
    return {"status": "resumed"}

# Scope
@router.get("/{eng_id}/scope/targets")
async def list_targets(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(ScopeTarget).where(ScopeTarget.engagement_id == eng_id))
    return result.scalars().all()

@router.post("/{eng_id}/scope/targets")
async def add_target(eng_id: str, payload: ScopeTargetIn, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    eng = (await db.execute(select(Engagement).where(Engagement.id == eng_id))).scalar_one_or_none()
    if not eng:
        raise HTTPException(status_code=404, detail="Engagement not found")
    t = ScopeTarget(engagement_id=eng_id, target_type=payload.target_type, value=payload.value, description=payload.description)
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return t

@router.delete("/{eng_id}/scope/targets/{tid}")
async def del_target(eng_id: str, tid: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(ScopeTarget).where(ScopeTarget.id == tid, ScopeTarget.engagement_id == eng_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(t)
    await db.commit()
    return {"deleted": tid}

@router.get("/{eng_id}/scope/exclusions")
async def list_exclusions(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(ScopeExclusion).where(ScopeExclusion.engagement_id == eng_id))
    return result.scalars().all()

@router.post("/{eng_id}/scope/exclusions")
async def add_exclusion(eng_id: str, payload: ScopeExclusionIn, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    e = ScopeExclusion(engagement_id=eng_id, exclusion_type=payload.exclusion_type, value=payload.value, reason=payload.reason)
    db.add(e)
    await db.commit()
    await db.refresh(e)
    return e

@router.post("/{eng_id}/scope/validate")
async def validate_scope(eng_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    targets = (await db.execute(select(ScopeTarget).where(ScopeTarget.engagement_id == eng_id))).scalars().all()
    exclusions = (await db.execute(select(ScopeExclusion).where(ScopeExclusion.engagement_id == eng_id))).scalars().all()
    scope_targets = [{"target_type": t.target_type, "value": t.value} for t in targets]
    excl = [{"exclusion_type": e.exclusion_type, "value": e.value} for e in exclusions]
    result = ScopeGuard.evaluate(payload.get("target",""), payload.get("target_type","ip"), scope_targets, excl, port=payload.get("port"), technique=payload.get("technique"))
    return result
