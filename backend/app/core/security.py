from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from .config import settings
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PLACEHOLDER_SECRETS = {"change-me-to-32+random-chars-in-production", "change-me", ""}


def assert_production_secrets() -> None:
    """Fail fast on unsafe defaults when ENV=production."""
    if not settings.is_production():
        return
    if settings.JWT_SECRET in PLACEHOLDER_SECRETS or len(settings.JWT_SECRET) < 32:
        raise RuntimeError("JWT_SECRET must be changed in production (32+ random chars)")
    # Database URL must not contain known dev placeholders / empty passwords.
    db = settings.DATABASE_URL or ""
    for bad in ("redforge_secret_2026", "CHANGE_ME", "change-me", "password@", "://redforge:@", "://redforge:pass@"):
        if bad in db:
            raise RuntimeError("DATABASE_URL contains placeholder credentials in production")
    if "localhost" in db or "127.0.0.1" in db:
        raise RuntimeError("DATABASE_URL must point at managed Postgres in production, not localhost")
    if not settings.SEED_ADMIN_PASSWORD and settings.SEED_ADMIN_ON_BOOT:
        # Warn-only: admin seed skipped (logged in main.py). Enforce explicit opt-out instead.
        import logging
        logging.getLogger("redforge").warning("SEED_ADMIN_PASSWORD empty in production — admin seed skipped")


def hash_password(password: str) -> str:
    if not password or len(password) < 8 or len(password) > 128:
        raise ValueError("Password must be 8-128 characters")
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str):
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e
