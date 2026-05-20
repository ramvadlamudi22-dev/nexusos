"""Runtime models - Pydantic models for runtime entities."""

import hashlib
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class RuntimeState(str, Enum):
    """Lifecycle states for a runtime instance."""

    INITIALIZING = "INITIALIZING"
    READY = "READY"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


def generate_runtime_id(name: str, creation_timestamp: str) -> str:
    """Generate a deterministic runtime ID from name and creation timestamp.

    Uses SHA-256 hash of (name + creation_timestamp) for reproducibility.
    Same inputs always produce the same ID.
    """
    content = f"{name}{creation_timestamp}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


class Runtime(BaseModel):
    """A governed runtime instance with explicit state."""

    id: str
    name: str
    state: RuntimeState = RuntimeState.INITIALIZING
    metadata: Dict[str, Any] = Field(default_factory=dict)
    creation_timestamp: str

    model_config = {"use_enum_values": False}


class RuntimeRegistration(BaseModel):
    """Request body for registering a new runtime."""

    name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
