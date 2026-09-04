from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
import redis.asyncio as redis
from ...core.config import settings

router = APIRouter()

@router.get("")
async def health(db: AsyncSession = Depends(get_db)):
    checks = {}
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
    try:
        r = redis.from_url(settings.REDIS_URL)
        await r.ping()
        checks["redis"] = "ok"
        await r.close()
    except Exception as e:
        checks["redis"] = f"error: {e}"
    checks["api"] = "ok"
    return {"status": "healthy" if checks.get("database")=="ok" else "degraded", "checks": checks}
