from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.security import verify_password, hash_password, create_access_token
from ...models.user import User
from ...schemas.auth import LoginRequest, TokenResponse, UserOut
from ...core.deps import get_current_user

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

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
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="User already exists")
    new_user = User(email=email, hashed_password=hash_password(password), full_name=payload.get("full_name",""), role=payload.get("role","operator"))
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user
