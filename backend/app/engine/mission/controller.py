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

# Kill switch state per engagement (in-memory; Redis-backed in clustered prod via API layer).
_kill_switches: dict[str, dict] = {}

def activate_kill_switch(engagement_id: str, reason: str = "Emergency stop"):
    _kill_switches[engagement_id] = {"active": True, "engagement_id": engagement_id, "reason": reason}
    return _kill_switches[engagement_id]

def clear_kill_switch(engagement_id: str | None = None):
    if engagement_id:
        _kill_switches.pop(engagement_id, None)
    else:
        _kill_switches.clear()
    return {"active": False, "engagement_id": engagement_id, "reason": ""}

def is_killed(engagement_id: str | None = None) -> bool:
    if not engagement_id:
        return bool(_kill_switches)
    return _kill_switches.get(engagement_id, {}).get("active", False)

# Back-compat alias for single global view (deprecated).
_kill_switch = {"active": False, "engagement_id": None, "reason": ""}
