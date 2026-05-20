"""Browser runtime models - Pydantic models for browser session entities."""

from enum import Enum
from typing import Dict, List

from pydantic import BaseModel, Field


class BrowserSessionState(str, Enum):
    """Lifecycle states for a browser session."""

    INITIALIZING = "INITIALIZING"
    ACTIVE = "ACTIVE"
    RECORDING = "RECORDING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class BrowserActionType(str, Enum):
    """Types of browser actions."""

    NAVIGATE = "NAVIGATE"
    CLICK = "CLICK"
    TYPE = "TYPE"
    SCREENSHOT = "SCREENSHOT"
    WAIT = "WAIT"


class BrowserAction(BaseModel):
    """A browser action to execute."""

    action_type: BrowserActionType
    target: str
    value: str = ""
    timestamp: str = ""


class BrowserActionResult(BaseModel):
    """Result of executing a browser action."""

    success: bool
    action: BrowserAction
    screenshot_path: str = ""
    timestamp: str
    error: str = ""


class BrowserSession(BaseModel):
    """A browser session with state and recording."""

    id: str
    url: str
    state: BrowserSessionState
    creation_timestamp: str
    screenshots: List[str] = Field(default_factory=list)
    recording: List[Dict] = Field(default_factory=list)
