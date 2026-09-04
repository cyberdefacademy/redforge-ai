from fastapi import APIRouter, Depends, HTTPException
from ...core.deps import get_current_user
from ...models.user import User
from ...tools.registry.registry import load_registry, get_tool
from ...tools.adapters.base import build_command, validate_params
from ...tools.sandbox.executor import execute_sandboxed
from ...engine.scope.guard import ScopeGuard
from ...engine.risk.engine import evaluate_risk
from ...engine.mission.controller import is_killed
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...models.scope import ScopeTarget, ScopeExclusion
from ...models.asset import Task, AuditLog
import uuid

router = APIRouter()

@router.get("")
async def list_tools(user: User = Depends(get_current_user)):
    return load_registry()

@router.get("/{name}")
async def get_tool_detail(name: str, user: User = Depends(get_current_user)):
    t = get_tool(name)
    if not t:
        raise HTTPException(status_code=404, detail="Tool not found")
    return t

@router.post("/execute")
async def execute_tool(payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    tool = payload.get("tool")
    target = payload.get("target")
    engagement_id = payload.get("engagement_id")
    params = payload.get("params", {})
    params["target"] = target

    if not tool or not target:
        raise HTTPException(status_code=400, detail="tool and target required")

    # Kill switch check
    if is_killed(engagement_id):
        raise HTTPException(status_code=423, detail="Emergency stop active - execution blocked")

    # Scope validation if engagement provided
    if engagement_id:
        targets = (await db.execute(select(ScopeTarget).where(ScopeTarget.engagement_id == engagement_id))).scalars().all()
        exclusions = (await db.execute(select(ScopeExclusion).where(ScopeExclusion.engagement_id == engagement_id))).scalars().all()
        st = [{"target_type": t.target_type, "value": t.value} for t in targets]
        ex = [{"exclusion_type": e.exclusion_type, "value": e.value} for e in exclusions]
        # Determine target_type
        ttype = "ip" if target.replace(".","").isdigit() else "domain" if "." in target and not target.startswith("http") else "url"
        verdict = ScopeGuard.evaluate(target, ttype, st, ex)
        if not verdict["allowed"]:
            db.add(AuditLog(engagement_id=engagement_id, actor=user.email, action="scope_violation", target=target, tool=tool, result="blocked", metadata_json=str(verdict)))
            await db.commit()
            raise HTTPException(status_code=403, detail=verdict["reason"])

    # Risk check
    risk = evaluate_risk(tool, target)
    if risk["requires_approval"] and not payload.get("approved"):
        # Create waiting task
        task = Task(engagement_id=engagement_id or "global", type="tool_execution", status="waiting_approval", tool=tool, target=target, risk_level=risk["risk"], created_by=user.id)
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return {"status": "waiting_approval", "task_id": task.id, "risk": risk, "message": "Approval required"}

    # Validate params
    ok, msg = validate_params(tool, params)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    cmd = build_command(tool, params)
    if not cmd:
        raise HTTPException(status_code=400, detail=f"No adapter for tool {tool}")

    # Execute sandboxed
    result = await execute_sandboxed(cmd, timeout=300, engagement_id=engagement_id or "", tool=tool, target=target, operator=user.email)

    # Audit
    db.add(AuditLog(engagement_id=engagement_id, actor=user.email, action="tool_execute", target=target, tool=tool, result="completed" if result["exit_code"]==0 else "failed", metadata_json=str({"risk": risk, "exit_code": result["exit_code"]})[:2000]))
    await db.commit()

    return {"tool": tool, "target": target, "risk": risk, "result": result}

@router.post("/discover")
async def discover(user: User = Depends(get_current_user)):
    return {"tools": load_registry(), "discovered_at": "now"}
