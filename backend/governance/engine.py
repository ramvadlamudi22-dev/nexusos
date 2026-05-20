"""Governance engine - policy enforcement, permission checks, action validation."""

from typing import Dict, List, Optional

from backend.governance.models import (
    Permission,
    PermissionLevel,
    Policy,
    ValidationResult,
)
from backend.runtime.context import RuntimeExecutionContext


class GovernanceEngine:
    """Enforces governance policies on all runtime actions.

    All actions must be validated before execution.
    Governance is structural, not advisory.
    """

    def __init__(self, context: RuntimeExecutionContext):
        """Initialize the governance engine.

        Args:
            context: Execution context providing time source.
        """
        self._context = context
        self._policies: Dict[str, Policy] = {}

    def register_policy(self, policy: Policy) -> None:
        """Register a governance policy.

        Args:
            policy: The policy to register.
        """
        self._policies[policy.id] = policy

    def remove_policy(self, policy_id: str) -> bool:
        """Remove a governance policy.

        Args:
            policy_id: ID of the policy to remove.

        Returns:
            True if the policy was found and removed, False otherwise.
        """
        if policy_id in self._policies:
            del self._policies[policy_id]
            return True
        return False

    def validate_action(self, action: str, resource: str = "*") -> ValidationResult:
        """Validate an action against all active policies.

        Checks all registered policies. If any policy explicitly denies
        the action, it is denied. If no policy allows it, it is denied
        by default (deny-by-default governance).

        Args:
            action: The action being attempted.
            resource: The resource the action targets.

        Returns:
            ValidationResult indicating whether the action is permitted.
        """
        for policy_id, policy in self._policies.items():
            if not policy.active:
                continue

            for permission in policy.permissions:
                if permission.action == action or permission.action == "*":
                    if permission.resource == resource or permission.resource == "*":
                        if permission.level == PermissionLevel.DENY:
                            return ValidationResult(
                                permitted=False,
                                action=action,
                                reason=f"Denied by policy: {policy.name}",
                                policy_id=policy_id,
                            )
                        elif permission.level == PermissionLevel.ALLOW:
                            return ValidationResult(
                                permitted=True,
                                action=action,
                                reason=f"Allowed by policy: {policy.name}",
                                policy_id=policy_id,
                            )

        # Default deny - no policy explicitly allows the action
        return ValidationResult(
            permitted=False,
            action=action,
            reason="No policy permits this action (default deny)",
        )

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a specific policy by ID."""
        return self._policies.get(policy_id)

    def list_policies(self) -> List[Policy]:
        """List all registered policies."""
        return list(self._policies.values())

    @property
    def policy_count(self) -> int:
        """Get the number of registered policies."""
        return len(self._policies)

    @property
    def active(self) -> bool:
        """Whether the governance engine is active (has policies)."""
        return len(self._policies) > 0
