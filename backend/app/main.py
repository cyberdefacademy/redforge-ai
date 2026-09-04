from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .core.config import settings
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "admin@redforge.local"))
        if not result.scalar_one_or_none():
            admin = User(email="admin@redforge.local", hashed_password=hash_password("RedForge!2026"), full_name="RedForge Admin", role="administrator")
            session.add(admin)
            await session.commit()
            print("[REDFORGE] Seeded admin@redforge.local / RedForge!2026")
        result = await session.execute(select(Tool))
        if not result.scalars().first():
            from .tools.registry.registry import load_registry
            for t in load_registry():
                session.add(Tool(name=t["name"], executable=t["executable"], category=t["category"], risk_level=t["risk_level"], status=t["status"], version="unknown"))
            await session.commit()
    yield

app = FastAPI(title="REDFORGE AI", description="Autonomous Red Team Mission Control", version="0.7.1", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
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

@app.get("/")
async def root():
    return {"name": "REDFORGE AI", "version": "0.7.1", "status": "operational", "docs": "/docs"}

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
@app.websocket("/ws/engagements/{eng_id}")
async def ws_engagement(websocket: WebSocket, eng_id: str):
    await websocket.accept()
    if eng_id not in connections: connections[eng_id] = []
    connections[eng_id].append(websocket)
    try:
        await websocket.send_json({"type":"connected","engagement_id": eng_id})
        while True:
            data = await websocket.receive_text()
            for ws in connections[eng_id]:
                await ws.send_json({"type":"message","data": data})
    except WebSocketDisconnect:
        connections[eng_id].remove(websocket)
