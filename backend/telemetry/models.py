"""Telemetry models - metrics, traces, and health state."""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class HealthState(str, Enum):
    """System health states."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


class MetricRecord(BaseModel):
    """A single metric measurement."""

    name: str
    value: float
    timestamp: str
    labels: Dict[str, str] = Field(default_factory=dict)


class TraceRecord(BaseModel):
    """A single execution trace."""

    trace_id: str
    operation: str
    start_timestamp: str
    end_timestamp: str = ""
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
