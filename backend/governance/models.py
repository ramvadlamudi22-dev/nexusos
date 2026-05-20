"""Governance models - policies, permissions, and validation results."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PermissionLevel(str, Enum):
    """Permission levels for governance."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    AUDIT = "AUDIT"


class Permission(BaseModel):
    """A single permission entry."""

    action: str
    level: PermissionLevel = PermissionLevel.DENY
    resource: str = "*"


class Policy(BaseModel):
    """A governance policy containing permissions."""

    id: str
    name: str
    description: str = ""
    permissions: List[Permission] = Field(default_factory=list)
    active: bool = True


class ValidationResult(BaseModel):
    """Result of a governance validation check."""

    permitted: bool
    action: str
    reason: str = ""
    policy_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
