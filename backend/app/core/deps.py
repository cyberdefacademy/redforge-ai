from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .database import get_db
from .security import decode_token
from .config import settings
from ..models.user import User

security = HTTPBearer(auto_error=False)

# Shared redis client for token denylist (pooled; fail-closed in production)
_revoked_cache: set[str] = set()
_revoked_cache_max = 10000
_redis_client = None


async def _get_redis():
    global _redis_client
    try:
        import redis.asyncio as redis
        if _redis_client is None:
            _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=2)
        return _redis_client
    except Exception:
        return None


async def is_token_revoked(jti: str) -> bool:
    if not jti:
        return False
    if jti in _revoked_cache:
        return True
    try:
        r = await _get_redis()
        if r is None:
            # Fail-closed in production: deny on infra outage; fail-open in dev for operability.
            return settings.is_production()
        exists = await r.exists(f"revoked:{jti}")
        return bool(exists)
    except Exception:
        return settings.is_production()


async def revoke_token(jti: str, ttl_seconds: int = 86400 * 8) -> None:
    if jti:
        _revoked_cache.add(jti)
        # Bound in-process cache to avoid unbounded growth with multiple workers.
        if len(_revoked_cache) > _revoked_cache_max:
            _revoked_cache.pop()
    try:
        r = await _get_redis()
        if r is not None:
            await r.setex(f"revoked:{jti}", ttl_seconds, "1")
    except Exception:
        pass


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type", "access") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        if await is_token_revoked(payload.get("jti", "")):
            raise HTTPException(status_code=401, detail="Token revoked")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def require_roles(*roles: str):
    async def checker(user: User = Depends(get_current_user)) -> User:
        if roles and user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return user
    return checker
