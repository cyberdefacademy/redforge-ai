from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.user import User
from ...models.asset import Host, Port, Service, Finding
import uuid

router = APIRouter()

def build_graph(hosts, ports_map, findings):
    nodes=[]
    edges=[]
    # host nodes
    for h in hosts:
        nodes.append({"id": h.id, "type":"host", "data":{"label": h.ip, "hostname": h.hostname, "os": h.os}, "position":{"x": 0, "y": 0}})
        for p in ports_map.get(h.id, []):
            nid = p.id
            nodes.append({"id": nid, "type":"port", "data":{"label": f"{p.port}/{p.protocol} {p.state}"}, "position":{"x":0,"y":0}})
            edges.append({"id": f"{h.id}-{nid}", "source": h.id, "target": nid, "label":"exposes"})
            # service nodes under port
            # need services per port; simplified
        # adversary entry edge from internet
        # create initial access path if finding exists
    for f in findings:
        fid = f.id
        nodes.append({"id": fid, "type":"finding", "data":{"label": f.title, "severity": f.severity, "cve": f.cve}, "position":{"x":0,"y":0}})
        # link to first host if matches asset ip
        for h in hosts:
            if h.ip in (f.asset or ""):
                edges.append({"id": f"{h.id}-{fid}", "source": h.id, "target": fid, "label":"vulnerable"})
    # auto-layout: simple dagre-like placement
    for i,n in enumerate(nodes):
        n["position"]={"x": (i%4)*250, "y": (i//4)*140}
    return {"nodes": nodes, "edges": edges}

@router.get("/engagements/{eng_id}/attack-graph")
async def attack_graph(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    hosts = (await db.execute(select(Host).where(Host.engagement_id==eng_id))).scalars().all()
    ports_map={}
    for h in hosts:
        pr = (await db.execute(select(Port).where(Port.host_id==h.id))).scalars().all()
        ports_map[h.id]=pr
    findings = (await db.execute(select(Finding).where(Finding.engagement_id==eng_id))).scalars().all()
    graph = build_graph(hosts, ports_map, findings)
    return graph

@router.get("/engagements/{eng_id}/attack-paths")
async def attack_paths(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    graph = await attack_graph(eng_id, db, user)
    # Derive prioritized paths: host -> port -> finding chains
    paths=[]
    for e in graph["edges"]:
        if "vulnerable" in e.get("label",""):
            paths.append({"id": str(uuid.uuid4()), "steps": [e["source"], e["target"]], "risk_score": 7.5, "mitre": ["T1190","T1046"]})
    if not paths and graph["nodes"]:
        # at least one recon path
        host_nodes = [n for n in graph["nodes"] if n["type"]=="host"]
        for h in host_nodes[:2]:
            paths.append({"id": str(uuid.uuid4()), "steps": [h["id"]], "risk_score": 3.0, "mitre": ["T1595"]})
    return {"paths": paths, "graph": graph}
