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
from ...models.scope import ScopeTarget, ScopeExclusion, Authorization
from ...models.asset import Task, AuditLog
from ...models.engagement import Engagement
import uuid
from urllib.parse import urlparse

router = APIRouter()

def _infer_target_type(target: str) -> str:
    t = (target or "").strip()
    if t.startswith("http://") or t.startswith("https://"):
        return "url"
    # Bare IP literal (v4/v6) — no dots heuristic.
    import ipaddress
    try:
        ipaddress.ip_address(t.split(":")[0].strip("[]") if t.count(":") == 1 else t.strip("[]"))
        return "ip"
    except ValueError:
        pass
    if "/" in t:
        # CIDR notation is scope definition, not a runnable target — treat as ip for guard matching.
        try:
            ipaddress.ip_network(t, strict=False)
            return "ip"
        except ValueError:
            pass
    return "domain" if "." in t else "hostname"

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
    params = dict(payload.get("params", {}) or {})
    if target:
        params["target"] = target

    if not tool or not target:
        raise HTTPException(status_code=400, detail="tool and target required")
    if not engagement_id:
        # Deny-by-default: every execution must be tied to an engagement (no global exec).
        raise HTTPException(status_code=422, detail="engagement_id is required")

    # Engagement must exist and be authorized before any tool runs.
    eng = (await db.execute(select(Engagement).where(Engagement.id == engagement_id))).scalar_one_or_none()
    if not eng:
        raise HTTPException(status_code=404, detail="Engagement not found")
    authz = (await db.execute(select(Authorization).where(Authorization.engagement_id == engagement_id))).scalar_one_or_none()
    if not authz or not authz.confirmed or eng.status not in ("authorized", "running"):
        db.add(AuditLog(engagement_id=engagement_id, actor=user.email, action="unauthorized_execute_blocked", target=target, tool=tool, result="blocked", metadata_json="engagement not authorized"))
        await db.commit()
        raise HTTPException(status_code=403, detail="Engagement is not authorized for execution")

    # Kill switch check (per-engagement)
    if is_killed(engagement_id):
        raise HTTPException(status_code=423, detail="Emergency stop active - execution blocked")

    # Scope validation (always, when engagement provided)
    targets = (await db.execute(select(ScopeTarget).where(ScopeTarget.engagement_id == engagement_id))).scalars().all()
    exclusions = (await db.execute(select(ScopeExclusion).where(ScopeExclusion.engagement_id == engagement_id))).scalars().all()
    st = [{"target_type": t.target_type, "value": t.value} for t in targets]
    ex = [{"exclusion_type": e.exclusion_type, "value": e.value} for e in exclusions]
    ttype = _infer_target_type(target)
    verdict = ScopeGuard.evaluate(target, ttype, st, ex, port=payload.get("port"), technique=payload.get("technique"))
    if not verdict["allowed"]:
        db.add(AuditLog(engagement_id=engagement_id, actor=user.email, action="scope_violation", target=target, tool=tool, result="blocked", metadata_json=str(verdict)))
        await db.commit()
        raise HTTPException(status_code=403, detail=verdict["reason"])

    # Risk check — approval must be a lead/admin grant on an existing waiting task, never a client boolean.
    risk = evaluate_risk(tool, target, mode=payload.get("mode", "enumeration"))
    if risk["requires_approval"]:
        task_id = payload.get("task_id")
        approved = False
        if task_id:
            task = (await db.execute(select(Task).where(Task.id == task_id, Task.engagement_id == engagement_id))).scalar_one_or_none()
            if task and task.status == "queued" and user.role in ("administrator", "red_team_lead"):
                approved = True
        if not approved:
            # Create waiting task
            task = Task(engagement_id=engagement_id, type="tool_execution", status="waiting_approval", tool=tool, target=target, risk_level=risk["risk"], created_by=user.id)
            db.add(task)
            await db.commit()
            await db.refresh(task)
            return {"status": "waiting_approval", "task_id": task.id, "risk": risk, "message": "Approval required from lead/admin"}

    # Validate params
    ok, msg = validate_params(tool, params)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)

    cmd = build_command(tool, params)
    if not cmd:
        raise HTTPException(status_code=400, detail=f"No adapter for tool {tool} or invalid params")

    # Execute sandboxed (per-tool timeout from registry)
    reg = get_tool(tool) or {}
    timeout = int(reg.get("timeout", 300) or 300)
    result = await execute_sandboxed(cmd, timeout=timeout, engagement_id=engagement_id or "", tool=tool, target=target, operator=user.email)

    # Audit
    db.add(AuditLog(engagement_id=engagement_id, actor=user.email, action="tool_execute", target=target, tool=tool, result="completed" if result["exit_code"]==0 else "failed", metadata_json=str({"risk": risk, "exit_code": result["exit_code"]})[:2000]))
    await db.commit()

    return {"tool": tool, "target": target, "risk": risk, "result": result}

@router.post("/discover")
async def discover(user: User = Depends(get_current_user)):
    return {"tools": load_registry(), "discovered_at": "now"}
