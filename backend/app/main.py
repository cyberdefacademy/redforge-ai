from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from logging.config import dictConfig
from .core.config import settings
from .core.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from .core.security import assert_production_secrets
from .core.database import engine, Base, SessionLocal
from .api.v1.auth import router as auth_router
from .api.v1.engagements import router as eng_router
from .api.v1.tools import router as tools_router
from .api.v1.assets import router as assets_router
from .api.v1.health import router as health_router
from .api.v1.evidence import router as evidence_router
from .api.v1.lab import router as lab_router
from .api.v1.recon import router as recon_router
from .api.v1.agents import router as agents_router
from .api.v1.graph import router as graph_router
from .api.v1.reports import router as reports_router
from .api.v1.correlation import router as corr_router
from .api.v1.advanced import router as advanced_router
from .api.v1.health_center import router as health_center_router
from sqlalchemy import select
from .models.user import User
from .models.engagement import Engagement
from .models.scope import ScopeTarget, ScopeExclusion, Authorization
from .models.asset import Host, Port, Service, Finding, Evidence, Task, Tool, AuditLog
from .core.security import hash_password

logger = logging.getLogger("redforge")

dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"json": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
    "handlers": {"default": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["default"], "level": settings.LOG_LEVEL.upper()},
})

@asynccontextmanager
async def lifespan(app: FastAPI):
    assert_production_secrets()
    if not settings.is_production():
        # Dev convenience: ensure tables exist. Prod uses Alembic via entrypoint.
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    if settings.SEED_ADMIN_ON_BOOT:
        async with SessionLocal() as session:
            result = await session.execute(select(User).where(User.email == settings.SEED_ADMIN_EMAIL))
            if not result.scalar_one_or_none():
                password = settings.SEED_ADMIN_PASSWORD
                if settings.is_production():
                    if not password:
                        logger.warning("SEED_ADMIN_ON_BOOT=true but SEED_ADMIN_PASSWORD empty — skipping admin seed")
                    else:
                        admin = User(email=settings.SEED_ADMIN_EMAIL, hashed_password=hash_password(password), full_name="RedForge Admin", role="administrator")
                        session.add(admin)
                        await session.commit()
                        logger.info("Seeded admin %s", settings.SEED_ADMIN_EMAIL)
                else:
                    admin = User(email=settings.SEED_ADMIN_EMAIL, hashed_password=hash_password(password or "RedForge!2026"), full_name="RedForge Admin", role="administrator")
                    session.add(admin)
                    await session.commit()
                    print(f"[REDFORGE] Seeded {settings.SEED_ADMIN_EMAIL}")
            result = await session.execute(select(Tool))
            if not result.scalars().first():
                from .tools.registry.registry import load_registry
                for t in load_registry():
                    session.add(Tool(name=t["name"], executable=t["executable"], category=t["category"], risk_level=t["risk_level"], status=t["status"], version="unknown"))
                await session.commit()
    yield

app = FastAPI(
    title="REDFORGE AI",
    description="Autonomous Red Team Mission Control",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production() else "/admin/docs",
    redoc_url=None if settings.is_production() else "/redoc",
    openapi_url="/openapi.json" if not settings.is_production() else "/admin/openapi.json",
)
from starlette.middleware.trustedhost import TrustedHostMiddleware
if settings.is_production():
    # Restrict Host header to configured CORS origins + service names (SSRF/host-poisoning guard).
    allowed = set()
    for o in settings.cors_origin_list():
        try:
            from urllib.parse import urlparse
            allowed.add(urlparse(o).hostname or o)
        except Exception:
            pass
    allowed.update({"localhost", "api", "redforge-api"})
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(allowed))
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(eng_router, prefix="/api/v1/engagements", tags=["engagements"])
app.include_router(tools_router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(assets_router, prefix="/api/v1", tags=["assets"])
app.include_router(health_router, prefix="/api/v1/health", tags=["health"])
app.include_router(evidence_router, prefix="/api/v1", tags=["evidence"])
app.include_router(lab_router, prefix="/api/v1", tags=["lab"])
app.include_router(recon_router, prefix="/api/v1", tags=["recon"])
app.include_router(agents_router, prefix="/api/v1", tags=["agents"])
app.include_router(graph_router, prefix="/api/v1", tags=["graph"])
app.include_router(reports_router, prefix="/api/v1", tags=["reports"])
app.include_router(corr_router, prefix="/api/v1", tags=["correlation"])
app.include_router(advanced_router, prefix="/api/v1", tags=["advanced"])
app.include_router(health_center_router, prefix="/api/v1", tags=["health-center"])

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics (unauthenticated liveness-style counters; detailed app metrics behind admin)."""
    try:
        from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest, REGISTRY
        return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
    except Exception:
        return {"status": "metrics_unavailable"}


@app.get("/")
async def root():
    if settings.is_production():
        return {"status": "operational"}
    return {"name": "REDFORGE AI", "version": "1.0.0", "status": "operational", "docs": "/docs"}

@app.get("/api/v1/mitre/techniques")
async def mitre_techniques():
    return [
        {"id":"T1595","tactic":"Reconnaissance","name":"Active Scanning"},
        {"id":"T1590","tactic":"Reconnaissance","name":"Gather Victim Network Info"},
        {"id":"T1190","tactic":"Initial Access","name":"Exploit Public-Facing Application"},
        {"id":"T1046","tactic":"Discovery","name":"Network Service Discovery"},
        {"id":"T1078","tactic":"Persistence","name":"Valid Accounts"},
        {"id":"T1110","tactic":"Credential Access","name":"Brute Force"},
        {"id":"T1021","tactic":"Lateral Movement","name":"Remote Services"},
        {"id":"T1041","tactic":"Exfiltration","name":"Exfiltration Over C2"},
    ]

connections: dict[str, list[WebSocket]] = {}

async def _authenticate_ws(websocket: WebSocket):
    """Authenticate WS via ?token= JWT. Returns User or None."""
    token = websocket.query_params.get("token")
    if not token:
        return None
    try:
        from .core.security import decode_token
        from .core.deps import is_token_revoked
        payload = decode_token(token)
        if payload.get("type", "access") != "access":
            return None
        if await is_token_revoked(payload.get("jti", "")):
            return None
        async with SessionLocal() as session:
            result = await session.execute(select(User).where(User.id == payload.get("sub")))
            user = result.scalar_one_or_none()
            if not user or not user.is_active:
                return None
            return user
    except Exception:
        return None


@app.websocket("/ws/engagements/{eng_id}")
async def ws_engagement(websocket: WebSocket, eng_id: str):
    user = await _authenticate_ws(websocket)
    if not user:
        await websocket.close(code=4401)
        return
    # Engagement membership check: operator must own or the engagement must exist.
    try:
        from sqlalchemy import select as _select
        from .models.engagement import Engagement as _Eng
        async with SessionLocal() as _s:
            _eng = (await _s.execute(_select(_Eng).where(_Eng.id == eng_id))).scalar_one_or_none()
            if not _eng:
                await websocket.close(code=4404)
                return
    except Exception:
        pass
    await websocket.accept()
    if eng_id not in connections: connections[eng_id] = []
    connections[eng_id].append(websocket)
    try:
        await websocket.send_json({"type":"connected","engagement_id": eng_id})
        while True:
            data = await websocket.receive_text()
            if len(data) > 8192:
                await websocket.send_json({"type":"error","detail":"message too large"})
                continue
            for ws in connections[eng_id]:
                await ws.send_json({"type":"message","data": data})
    except WebSocketDisconnect:
        connections[eng_id].remove(websocket)
