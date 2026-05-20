"""Skills runtime models - Pydantic models for skill entities."""

from typing import Any, Dict

from pydantic import BaseModel, Field


class SkillDefinition(BaseModel):
    """Definition of a registered skill."""

    id: str
    name: str
    description: str = ""
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0.0"


class SkillInvocation(BaseModel):
    """A request to invoke a skill."""

    skill_id: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = ""


class SkillResult(BaseModel):
    """Result of invoking a skill."""

    skill_id: str
    outputs: Dict[str, Any] = Field(default_factory=dict)
    success: bool
    duration_ms: float = 0.0
    timestamp: str
    error: str = ""
