from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.user import User
from ...core.config import settings
from ...ai.providers.base import OllamaProvider, OpenAICompatibleProvider
from ...ai.agents.planner import plan_next_actions
import json, uuid
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

def get_provider(payload: dict | None = None):
    # Prefer Ollama; fallback to OpenAI-compatible if OLLAMA unreachable
    ollama_url = (payload or {}).get("ollama_url") or settings.OLLAMA_URL
    api_key = (payload or {}).get("api_key") or settings.OPENAI_API_KEY
    if api_key:
        return OpenAICompatibleProvider(base_url="https://api.openai.com", api_key=api_key)
    return OllamaProvider(base_url=ollama_url, model=(payload or {}).get("model","llama3.1"))

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
    return {"agents": AGENTS, "ollama_url": settings.OLLAMA_URL, "ollama_health": health}

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str, user: User = Depends(get_current_user)):
    for a in AGENTS:
        if a["id"]==agent_id:
            return a
    raise HTTPException(404, "Agent not found")

@router.post("/agents/{agent_id}/run")
async def run_agent(agent_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    agent = next((a for a in AGENTS if a["id"]==agent_id), None)
    if not agent:
        raise HTTPException(404, "Agent not found")
    engagement_id = payload.get("engagement_id")
    prompt = payload.get("prompt","Propose next 2 actions within scope for engagement %s" % engagement_id)
    context = {"agent": agent_id, "engagement_id": engagement_id, "user_prompt": prompt}
    evidence = payload.get("evidence", [])
    provider = get_provider(payload)
    result = await plan_next_actions(context, evidence, provider)
    return {"agent": agent_id, "engagement_id": engagement_id, "result": result, "provider": str(type(provider).__name__)}

@router.post("/agents/plan")
async def plan(payload: dict, user: User = Depends(get_current_user)):
    provider = get_provider(payload)
    ctx = payload.get("context", {"engagement_id": payload.get("engagement_id","unknown")})
    evidence = payload.get("evidence", [])
    result = await plan_next_actions(ctx, evidence, provider)
    return result
