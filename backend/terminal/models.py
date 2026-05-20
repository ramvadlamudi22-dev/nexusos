"""Terminal runtime models - Pydantic models for terminal session entities."""

from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field


class TerminalSessionState(str, Enum):
    """Lifecycle states for a terminal session."""

    IDLE = "IDLE"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class TerminalCommand(BaseModel):
    """A terminal command to execute."""

    command: str
    working_dir: str = "/tmp"
    timeout_seconds: int = 30
    environment: Dict[str, str] = Field(default_factory=dict)


class TerminalResult(BaseModel):
    """Result of executing a terminal command."""

    command: str
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    timestamp: str


class TerminalSession(BaseModel):
    """A terminal session with command history."""

    id: str
    state: TerminalSessionState
    command_history: List[TerminalResult] = Field(default_factory=list)
    creation_timestamp: str
