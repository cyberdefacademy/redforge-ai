from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.user import User
from ...models.engagement import Engagement
from ...models.scope import ScopeTarget, ScopeExclusion, Authorization
from ...models.asset import Host, Port, Finding
from ...core.config import settings
from ...ai.providers.base import (
    OllamaProvider,
    OpenAICompatibleProvider,
    get_provider as central_provider,
    resolve_local_model,
    redact_for_external,
)
from ...ai.providers.catalog import provider_spec, list_providers, PRESET_IDS
from ...ai.agents.planner import plan_next_actions, STAGE_SYSTEMS
import uuid
from datetime import datetime, timezone

router = APIRouter()

AGENTS = [
    {"id":"recon","name":"Recon Agent","category":"reconnaissance","model":"llama3.1","status":"ready","tools":["amass","subfinder","whatweb"]},
    {"id":"network","name":"Network Agent","category":"enumeration","model":"llama3.1","status":"ready","tools":["nmap","masscan"]},
    {"id":"web","name":"Web Agent","category":"web","model":"llama3.1","status":"ready","tools":["nuclei","gobuster","nikto"]},
    {"id":"ad","name":"AD Agent","category":"active_directory","model":"llama3.1","status":"ready","tools":["bloodhound"]},
    {"id":"cloud","name":"Cloud Agent","category":"cloud","model":"llama3.1","status":"ready","tools":["pacu","scoutsuite"]},
    {"id":"vuln","name":"Vuln Validation Agent","category":"vulnerability","model":"llama3.1","status":"ready","tools":["nuclei","searchsploit"]},
    {"id":"attack_path","name":"Attack Path Agent","category":"attack_graph","model":"llama3.1","status":"ready","tools":["graph-engine"]},
    {"id":"reporting","name":"Reporting Agent","category":"reporting","model":"llama3.1","status":"ready","tools":["evidence","findings"]},
]

AGENT_IDS = {a["id"] for a in AGENTS}


async def resolve_provider(payload: dict | None = None):
    """Provider selection with hybrid guardrails.

    Selection order: payload.provider -> settings.PROVIDER_DEFAULT.
    Local: resolved against live Ollama tags. Cloud: requires
    ENABLE_EXTERNAL_LLM or per-request enable_external:true, plus a configured
    key; prompts are redacted before leaving the lab.
    Legacy payload.api_key maps to the openai preset for backward compat.
    Returns (provider, label). Raises HTTPException on misconfiguration.
    """
    from fastapi import HTTPException as _HTTPException
    payload = dict(payload or {})
    provider_id = payload.get("provider") or settings.PROVIDER_DEFAULT
    legacy_key = (payload.get("api_key") or "").strip()
    if legacy_key and not payload.get("provider"):
        # Backward compat: old callers passed a raw OpenAI key.
        if not (payload.get("enable_external") or settings.ENABLE_EXTERNAL_LLM):
            raise _HTTPException(403, "Cloud provider disabled: set ENABLE_EXTERNAL_LLM=true or pass enable_external:true")
        from ...ai.providers.catalog import sanitize_model
        try:
            model = sanitize_model(payload.get("model") or settings.AI_MODEL_EXTERNAL)
        except ValueError as e:
            raise _HTTPException(400, str(e))
        return OpenAICompatibleProvider(base_url="https://api.openai.com", api_key=legacy_key, model=model), f"openai:{model}"
    try:
        spec = provider_spec(provider_id, payload.get("model"), settings)
    except ValueError as e:
        raise _HTTPException(400, str(e))
    if spec["kind"] == "local":
        model = await resolve_local_model(spec["base_url"], spec["model"])
        return OllamaProvider(base_url=spec["base_url"], model=model), f"ollama:{model}"
    if not (payload.get("enable_external") or settings.ENABLE_EXTERNAL_LLM):
        raise _HTTPException(403, "Cloud provider disabled: set ENABLE_EXTERNAL_LLM=true or pass enable_external:true")
    return (
        OpenAICompatibleProvider(base_url=spec["base_url"], api_key=spec["api_key"], model=spec["model"]),
        f"{provider_id}:{spec['model']}",
    )


async def load_engagement_bundle(db: AsyncSession, engagement_id: str | None) -> dict:
    """Scope targets, exclusions, auth state, and asset summary for planner context."""
    bundle: dict = {"scope_targets": [], "exclusions": [], "authorization": {"confirmed": False}, "summary": {}}
    if not engagement_id:
        return bundle
    eng = (await db.execute(select(Engagement).where(Engagement.id == engagement_id))).scalar_one_or_none()
    if not eng:
        raise HTTPException(404, "Engagement not found")
    targets = (await db.execute(select(ScopeTarget).where(ScopeTarget.engagement_id == engagement_id))).scalars().all()
    exclusions = (await db.execute(select(ScopeExclusion).where(ScopeExclusion.engagement_id == engagement_id))).scalars().all()
    auth = (await db.execute(select(Authorization).where(Authorization.engagement_id == engagement_id))).scalar_one_or_none()
    hosts = (await db.execute(select(Host).where(Host.engagement_id == engagement_id))).scalars().all()
    findings = (await db.execute(select(Finding).where(Finding.engagement_id == engagement_id))).scalars().all()
    port_count = 0
    for h in hosts:
        ports = (await db.execute(select(Port).where(Port.host_id == h.id))).scalars().all()
        port_count += len(ports)
    bundle["scope_targets"] = [{"target_type": t.target_type, "value": t.value} for t in targets]
    bundle["exclusions"] = [{"exclusion_type": e.exclusion_type, "value": e.value} for e in exclusions]
    bundle["authorization"] = {"confirmed": bool(auth and auth.confirmed), "status": eng.status}
    bundle["summary"] = {
        "hosts": [{"ip": h.ip, "hostname": h.hostname} for h in hosts[:10]],
        "host_count": len(hosts),
        "port_count": port_count,
        "findings": [{"title": f.title, "severity": f.severity} for f in findings[:10]],
        "finding_count": len(findings),
    }
    return bundle


def shape_evidence_for_stage(agent_id: str, caller_evidence: list, summary: dict) -> list:
    """Stage-specific evidence shaping so each agent reasons over relevant state."""
    base = list(caller_evidence or [])
    if agent_id in ("recon", "network", "web", "ad", "cloud"):
        base.append({"known_hosts": summary.get("hosts", []), "scope_note": "propose only in-scope targets"})
    if agent_id in ("vuln", "attack_path", "reporting"):
        base.append({"findings": summary.get("findings", []), "counts": {k: summary.get(k) for k in ("host_count", "port_count", "finding_count")}})
    return base


@router.get("/agents")
async def list_agents(user: User = Depends(get_current_user)):
    # Probe Ollama health quick
    health = "unknown"
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2) as c:
            r = await c.get(f"{settings.OLLAMA_URL}/api/tags")
            health = "connected" if r.status_code==200 else f"http_{r.status_code}"
    except Exception as e:
        health = f"unreachable:{type(e).__name__}"
    agents = []
    for a in AGENTS:
        agents.append({**a, "stage_prompt": bool(a["id"] in STAGE_SYSTEMS)})
    return {"agents": agents, "ollama_url": settings.OLLAMA_URL, "ollama_health": health}

@router.get("/agents/providers")
async def list_model_providers(user: User = Depends(get_current_user)):
    """Selectable model providers: local Ollama models + cloud presets.

    Reports `configured` flags only — never key material.
    """
    local_models: list[str] = []
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{settings.OLLAMA_URL}/api/tags")
            if r.status_code == 200:
                local_models = [m.get("name", "") for m in r.json().get("models", []) if m.get("name")]
    except Exception:
        pass
    return list_providers(settings, local_models)

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, user: User = Depends(get_current_user)):
    for a in AGENTS:
        if a["id"]==agent_id:
            return {**a, "system_prompt": STAGE_SYSTEMS.get(agent_id, "")[:500]}
    raise HTTPException(404, "Agent not found")

@router.post("/agents/{agent_id}/run")
async def run_agent(agent_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, "Agent not found")
    engagement_id = payload.get("engagement_id")
    bundle = await load_engagement_bundle(db, engagement_id)
    prompt = payload.get("prompt", f"Propose next 2 actions within scope for engagement {engagement_id}")
    context = {
        "agent": agent_id,
        "engagement_id": engagement_id,
        "authorization": bundle["authorization"],
        "summary": bundle["summary"],
        "user_prompt": prompt,
    }
    # External prompts are redacted before leaving the lab when external LLM is on
    if payload.get("enable_external") or settings.ENABLE_EXTERNAL_LLM:
        context["user_prompt"] = redact_for_external(prompt)
    evidence = shape_evidence_for_stage(agent_id, payload.get("evidence", []), bundle["summary"])
    provider, provider_label = await resolve_provider(payload)
    result = await plan_next_actions(
        context, evidence, provider,
        scope_targets=bundle["scope_targets"], exclusions=bundle["exclusions"], agent_id=agent_id,
    )
    return {"agent": agent_id, "engagement_id": engagement_id, "result": result, "provider": provider_label}

@router.post("/agents/plan")
async def plan(payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    engagement_id = payload.get("engagement_id")
    agent_id = payload.get("agent_id", "recon")
    if agent_id not in AGENT_IDS:
        raise HTTPException(404, "Agent not found")
    bundle = await load_engagement_bundle(db, engagement_id)
    ctx = payload.get("context", {"engagement_id": engagement_id or "unknown"})
    ctx = {**ctx, "authorization": bundle["authorization"], "summary": bundle["summary"]}
    evidence = shape_evidence_for_stage(agent_id, payload.get("evidence", []), bundle["summary"])
    provider, _ = await resolve_provider(payload)
    return await plan_next_actions(
        ctx, evidence, provider,
        scope_targets=bundle["scope_targets"], exclusions=bundle["exclusions"], agent_id=agent_id,
    )
