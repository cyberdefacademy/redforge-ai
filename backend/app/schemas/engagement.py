from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EngagementCreate(BaseModel):
    name: str
    customer: str = ""
    description: str = ""
    assessment_type: str = "external"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class EngagementOut(BaseModel):
    id: str
    name: str
    customer: str
    description: str
    operator_id: str
    assessment_type: str
    status: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_at: datetime
    class Config:
        from_attributes = True

class ScopeTargetIn(BaseModel):
    target_type: str
    value: str
    description: str = ""

class ScopeExclusionIn(BaseModel):
    exclusion_type: str
    value: str
    reason: str = ""
