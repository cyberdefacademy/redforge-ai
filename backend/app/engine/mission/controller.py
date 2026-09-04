from enum import Enum

class EngagementStatus(str, Enum):
    DRAFT = "draft"
    AUTHORIZED = "authorized"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"

class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Kill switch state (in-memory + redis in prod)
_kill_switch = {"active": False, "engagement_id": None, "reason": ""}

def activate_kill_switch(engagement_id: str, reason: str = "Emergency stop"):
    _kill_switch.update({"active": True, "engagement_id": engagement_id, "reason": reason})
    return _kill_switch

def clear_kill_switch():
    _kill_switch.update({"active": False, "engagement_id": None, "reason": ""})
    return _kill_switch

def is_killed(engagement_id: str | None = None) -> bool:
    if not _kill_switch["active"]:
        return False
    if engagement_id and _kill_switch["engagement_id"] and _kill_switch["engagement_id"] != engagement_id:
        return False
    return True
