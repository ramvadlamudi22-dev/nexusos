"""Workflow engine models - Pydantic models for workflow entities."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowStepType(str, Enum):
    """Types of workflow steps."""

    BROWSER = "BROWSER"
    TERMINAL = "TERMINAL"
    SKILL = "SKILL"
    CUSTOM = "CUSTOM"


class WorkflowExecutionState(str, Enum):
    """Execution states for a workflow."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"


class WorkflowStep(BaseModel):
    """A single step in a workflow definition."""

    id: str
    name: str
    step_type: WorkflowStepType
    config: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)


class WorkflowStepResult(BaseModel):
    """Result of executing a workflow step."""

    step_id: str
    status: str
    outputs: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    error: str = ""


class WorkflowDefinition(BaseModel):
    """Definition of a workflow with ordered steps."""

    id: str
    name: str
    steps: List[WorkflowStep] = Field(default_factory=list)
    created_timestamp: str = ""


class WorkflowExecution(BaseModel):
    """Tracks the execution state of a workflow."""

    id: str
    workflow_id: str
    state: WorkflowExecutionState = WorkflowExecutionState.PENDING
    steps_completed: List[WorkflowStepResult] = Field(default_factory=list)
    current_step_id: Optional[str] = None
    start_timestamp: str = ""
    end_timestamp: str = ""
    results: Dict[str, Any] = Field(default_factory=dict)
