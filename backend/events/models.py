"""Event models - typed events with replay-safe structure."""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of events in the system."""

    RUNTIME = "RUNTIME"
    GOVERNANCE = "GOVERNANCE"
    TELEMETRY = "TELEMETRY"
    BROWSER = "BROWSER"
    TERMINAL = "TERMINAL"
    WORKFLOW = "WORKFLOW"
    SKILL = "SKILL"


class BaseEvent(BaseModel):
    """Base event with replay-safe structure including sequence numbers."""

    id: str
    event_type: EventType
    timestamp: str
    sequence: int
    payload: Dict[str, Any] = Field(default_factory=dict)


class RuntimeEvent(BaseEvent):
    """Event related to runtime lifecycle changes."""

    event_type: EventType = EventType.RUNTIME
    runtime_id: str = ""
    action: str = ""


class GovernanceEvent(BaseEvent):
    """Event related to governance decisions."""

    event_type: EventType = EventType.GOVERNANCE
    policy_id: str = ""
    decision: str = ""


class TelemetryEvent(BaseEvent):
    """Event related to telemetry observations."""

    event_type: EventType = EventType.TELEMETRY
    metric_name: str = ""
    value: Optional[float] = None
