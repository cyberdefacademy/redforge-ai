from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...core.database import get_db
from ...core.deps import get_current_user
from ...models.user import User
from ...models.asset import Finding
from collections import defaultdict

router = APIRouter()

SEV_WEIGHT = {"info":0,"low":1,"medium":2,"high":3,"critical":4}

@router.get("/engagements/{eng_id}/findings/correlated")
async def correlated(eng_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    findings = (await db.execute(select(Finding).where(Finding.engagement_id==eng_id))).scalars().all()
    # Group by title normalized
    groups=defaultdict(list)
    for f in findings:
        groups[f.title.lower().strip()].append(f)
    out=[]
    for title, items in groups.items():
        sev = max(items, key=lambda x: SEV_WEIGHT.get(x.severity,0)).severity
        cves = list({x.cve for x in items if x.cve})
        assets = list({x.asset for x in items if x.asset})
        out.append({"title": items[0].title, "count": len(items), "severity": sev, "cves": cves, "assets": assets, "confidence": "validated" if len(items)>1 else items[0].confidence, "ids":[x.id for x in items]})
    # sort by severity weight desc
    out.sort(key=lambda x: SEV_WEIGHT.get(x["severity"],0), reverse=True)
    return {"groups": out, "total": len(findings), "unique": len(out)}
