from fastapi import APIRouter, Depends, HTTPException, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.security import verify_password, hash_password, create_access_token, create_refresh_token, decode_token
from ...core.config import settings
from ...models.user import User
from ...schemas.auth import LoginRequest, TokenResponse, TokenPair, RefreshRequest, UserOut
from ...core.deps import get_current_user, revoke_token
import time

router = APIRouter()

_login_attempts: dict[str, list[float]] = {}
_MAX_ATTEMPTS = 10
_WINDOW_SECONDS = 60.0


def _throttle_login(key: str) -> None:
    now = time.monotonic()
    attempts = [t for t in _login_attempts.get(key, []) if now - t < _WINDOW_SECONDS]
    if len(attempts) >= _MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many login attempts, try again later")
    attempts.append(now)
    _login_attempts[key] = attempts


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    client_key = request.client.host if request.client else "unknown"
    _throttle_login(f"login:{client_key}:{payload.email}")
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    claims = {"sub": user.id, "email": user.email, "role": user.role}
    return {
        "access_token": create_access_token(claims),
        "refresh_token": create_refresh_token(claims),
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        data = decode_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    from ...core.deps import is_token_revoked
    if await is_token_revoked(data.get("jti", "")):
        raise HTTPException(status_code=401, detail="Token revoked")
    result = await db.execute(select(User).where(User.id == data.get("sub")))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    # Rotate: revoke old refresh token
    await revoke_token(data.get("jti", ""), ttl_seconds=settings.JWT_REFRESH_EXPIRE_DAYS * 86400)
    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
async def logout(payload: RefreshRequest | None = Body(default=None), request: Request = None, user: User = Depends(get_current_user)):
    # Revoke refresh token if supplied; also revoke the calling access token (jti from Authorization header).
    if payload and payload.refresh_token:
        try:
            data = decode_token(payload.refresh_token)
            await revoke_token(data.get("jti", ""))
        except Exception:
            pass
    try:
        auth = (request.headers.get("Authorization", "") if request else "")
        if auth.lower().startswith("bearer "):
            data = decode_token(auth.split(" ", 1)[1].strip())
            if data.get("type", "access") == "access":
                from ...core.config import settings as _s
                await revoke_token(data.get("jti", ""), ttl_seconds=_s.JWT_EXPIRE_MINUTES * 60)
    except Exception:
        pass
    return {"status": "logged_out"}

@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user

@router.post("/register", response_model=UserOut)
async def register(payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role not in ("administrator","red_team_lead"):
        raise HTTPException(status_code=403, detail="Insufficient privileges")
    email = payload.get("email")
    password = payload.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="email and password required")
    if len(password) < 12:
        raise HTTPException(status_code=400, detail="Password must be at least 12 characters")
    # Role assignment guard: only administrators can create administrators; leads can create operator/lead.
    requested_role = payload.get("role", "operator")
    allowed_roles = ("operator", "viewer")
    if user.role == "administrator":
        allowed_roles = ("operator", "viewer", "red_team_lead", "administrator")
    elif user.role == "red_team_lead":
        allowed_roles = ("operator", "viewer", "red_team_lead")
    if requested_role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Cannot assign requested role")
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User already exists")
    new_user = User(email=email, hashed_password=hash_password(password), full_name=payload.get("full_name",""), role=requested_role)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
