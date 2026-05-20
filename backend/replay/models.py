"""Replay models - deterministic operation recordings."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ReplayRecord(BaseModel):
    """A single replay record capturing an operation deterministically."""

    id: str
    operation: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str
    sequence: int
    checksum: str = ""
