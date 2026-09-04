import uuid, enum
from sqlalchemy import String, Text, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from ..core.database import Base

class AssessmentType(str, enum.Enum):
    external = "external"
    internal = "internal"
    web = "web"
    api = "api"
    wireless = "wireless"
    cloud = "cloud"
    ad = "ad"
    network = "network"
    red_team = "red_team"
    purple_team = "purple_team"
    adversary_simulation = "adversary_simulation"
    ctf = "ctf"

class EngagementStatus(str, enum.Enum):
    draft = "draft"
    authorized = "authorized"
    running = "running"
    paused = "paused"
    completed = "completed"
    archived = "archived"

class Engagement(Base):
    __tablename__ = "engagements"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(300))
    customer: Mapped[str] = mapped_column(String(300), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    operator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    assessment_type: Mapped[str] = mapped_column(String(50), default=AssessmentType.external)
    status: Mapped[str] = mapped_column(String(50), default=EngagementStatus.draft)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
