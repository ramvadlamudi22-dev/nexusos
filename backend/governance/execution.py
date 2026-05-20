"""Execution governance validator - validates runtime actions before execution."""

from typing import List

from backend.governance.engine import GovernanceEngine
from backend.governance.models import ValidationResult
from backend.runtime.context import RuntimeExecutionContext


# Dangerous URL schemes that should be blocked
BLOCKED_URL_SCHEMES = ["file://", "javascript:"]

# Dangerous terminal commands that should be blocked
BLOCKED_COMMANDS = ["shutdown", "reboot", "mkfs"]

# Patterns that need special handling (must match as whole target)
BLOCKED_RM_PATTERNS = ["rm -rf /"]

# Maximum steps allowed in a workflow
MAX_WORKFLOW_STEPS = 100

# Valid workflow step types
VALID_STEP_TYPES = {"BROWSER", "TERMINAL", "SKILL", "CUSTOM"}


class ExecutionGovernanceValidator:
    """Validates execution actions against governance policies.

    Enforces safety constraints on browser, terminal, workflow,
    and skill operations before they execute.
    """

    def __init__(
        self,
        context: RuntimeExecutionContext,
        governance_engine: GovernanceEngine,
    ):
        """Initialize the execution governance validator.

        Args:
            context: Runtime execution context.
            governance_engine: The underlying governance engine for policy checks.
        """
        self._context = context
        self._engine = governance_engine

    def validate_browser_action(self, action: dict) -> ValidationResult:
        """Validate a browser action before execution.

        Blocks dangerous URL schemes (file://, javascript:).

        Args:
            action: Dictionary with action details (must include 'target').

        Returns:
            ValidationResult indicating whether the action is permitted.
        """
        target = action.get("target", "")

        for scheme in BLOCKED_URL_SCHEMES:
            if target.lower().startswith(scheme):
                return ValidationResult(
                    permitted=False,
                    action="browser_action",
                    reason=f"Blocked URL scheme: {scheme}",
                )

        return ValidationResult(
            permitted=True,
            action="browser_action",
            reason="Browser action permitted",
        )

    def validate_terminal_command(self, command: str) -> ValidationResult:
        """Validate a terminal command before execution.

        Blocks dangerous commands (rm -rf /, shutdown, reboot, mkfs).

        Args:
            command: The command string to validate.

        Returns:
            ValidationResult indicating whether the command is permitted.
        """
        command_lower = command.lower().strip()

        # Check rm -rf / specifically (must target root, not a subdirectory)
        for pattern in BLOCKED_RM_PATTERNS:
            if pattern in command_lower:
                # Allow "rm -rf /some/path" but block "rm -rf /" and "rm -rf / "
                after = command_lower.split(pattern, 1)[1]
                if after == "" or after[0] == " " or after[0] == "\t":
                    return ValidationResult(
                        permitted=False,
                        action="terminal_command",
                        reason=f"Blocked dangerous command: {pattern}",
                    )

        for blocked in BLOCKED_COMMANDS:
            if blocked in command_lower:
                return ValidationResult(
                    permitted=False,
                    action="terminal_command",
                    reason=f"Blocked dangerous command: {blocked}",
                )

        return ValidationResult(
            permitted=True,
            action="terminal_command",
            reason="Terminal command permitted",
        )

    def validate_workflow_execution(self, workflow: dict) -> ValidationResult:
        """Validate a workflow before execution.

        Validates step count and step types.

        Args:
            workflow: Dictionary with workflow details (must include 'steps').

        Returns:
            ValidationResult indicating whether the workflow is permitted.
        """
        steps = workflow.get("steps", [])

        if len(steps) > MAX_WORKFLOW_STEPS:
            return ValidationResult(
                permitted=False,
                action="workflow_execution",
                reason=f"Workflow exceeds maximum step count ({MAX_WORKFLOW_STEPS})",
            )

        for step in steps:
            step_type = step.get("step_type", "").upper()
            if step_type and step_type not in VALID_STEP_TYPES:
                return ValidationResult(
                    permitted=False,
                    action="workflow_execution",
                    reason=f"Invalid step type: {step_type}",
                )

        return ValidationResult(
            permitted=True,
            action="workflow_execution",
            reason="Workflow execution permitted",
        )

    def validate_skill_invocation(
        self, invocation: dict, registered_skills: List[str]
    ) -> ValidationResult:
        """Validate a skill invocation before execution.

        Validates that the skill exists in the registry.

        Args:
            invocation: Dictionary with invocation details (must include 'skill_id').
            registered_skills: List of registered skill IDs.

        Returns:
            ValidationResult indicating whether the invocation is permitted.
        """
        skill_id = invocation.get("skill_id", "")

        if skill_id not in registered_skills:
            return ValidationResult(
                permitted=False,
                action="skill_invocation",
                reason=f"Skill not registered: {skill_id}",
            )

        return ValidationResult(
            permitted=True,
            action="skill_invocation",
            reason="Skill invocation permitted",
        )
