from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
import redis.asyncio as redis
import httpx
import os
from ...core.config import settings

router = APIRouter()

@router.get("")
async def health(db: AsyncSession = Depends(get_db)):
    checks = {}
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
    try:
        r = redis.from_url(settings.REDIS_URL, socket_timeout=2)
        await r.ping()
        checks["redis"] = "ok"
        await r.close()
    except Exception:
        checks["redis"] = "error"
    # Ollama reachability (non-fatal)
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"{settings.OLLAMA_URL.rstrip('/')}/api/tags")
            checks["ollama"] = "ok" if resp.status_code < 500 else "unavailable"
    except Exception:
        checks["ollama"] = "unreachable"
    # Evidence dir writable
    try:
        d = settings.EVIDENCE_DIR
        os.makedirs(d, exist_ok=True)
        checks["evidence_dir"] = "ok" if os.access(d, os.W_OK) else "not_writable"
    except Exception:
        checks["evidence_dir"] = "error"
    checks["api"] = "ok"
    status = "healthy" if checks.get("database") == "ok" else "degraded"
    return {"status": status, "checks": checks}
