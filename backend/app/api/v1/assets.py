from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.user import User
from ...models.asset import Host, Port, Service, Finding, Evidence, Task
from datetime import datetime

router = APIRouter()

@router.get("/engagements/{eng_id}/hosts")
async def list_hosts(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Host).where(Host.engagement_id == eng_id))
    return result.scalars().all()

@router.post("/engagements/{eng_id}/hosts")
async def create_host(eng_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    h = Host(engagement_id=eng_id, ip=payload.get("ip",""), hostname=payload.get("hostname",""), os=payload.get("os",""), status=payload.get("status","discovered"))
    db.add(h)
    await db.commit()
    await db.refresh(h)
    return h

@router.get("/hosts/{host_id}/ports")
async def list_ports(host_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Port).where(Port.host_id == host_id))
    return result.scalars().all()

@router.get("/engagements/{eng_id}/findings")
async def list_findings(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Finding).where(Finding.engagement_id == eng_id))
    return result.scalars().all()

@router.post("/engagements/{eng_id}/findings")
async def create_finding(eng_id: str, payload: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    f = Finding(engagement_id=eng_id, title=payload.get("title","Untitled"), severity=payload.get("severity","medium"), cve=payload.get("cve",""), cwe=payload.get("cwe",""), asset=payload.get("asset",""), confidence=payload.get("confidence","detected"), mitre_technique=payload.get("mitre_technique",""), evidence=payload.get("evidence",""))
    db.add(f)
    await db.commit()
    await db.refresh(f)
    return f

@router.get("/engagements/{eng_id}/tasks")
async def list_tasks(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Task).where(Task.engagement_id == eng_id).order_by(Task.created_at.desc()))
    return result.scalars().all()

@router.get("/engagements/{eng_id}/evidence")
async def list_evidence(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Evidence).where(Evidence.engagement_id == eng_id))
    return result.scalars().all()
