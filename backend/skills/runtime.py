"""Skills runtime - modular plugin registration and invocation."""

from typing import Any, Callable, Dict, List, Optional

from backend.runtime.context import RuntimeExecutionContext
from backend.skills.models import SkillDefinition, SkillInvocation, SkillResult


class SkillRuntime:
    """Manages skill registration and invocation.

    Skills are modular typed plugins with isolated execution boundaries.
    Each skill invocation is tracked for replay.
    """

    def __init__(self, context: RuntimeExecutionContext):
        """Initialize skill runtime with execution context.

        Args:
            context: Runtime execution context for deterministic timestamps.
        """
        self._context = context
        self._skills: Dict[str, SkillDefinition] = {}
        self._handlers: Dict[str, Callable] = {}

    def register_skill(
        self, definition: SkillDefinition, handler: Optional[Callable] = None
    ) -> None:
        """Register a skill definition with an optional handler.

        Args:
            definition: The skill definition to register.
            handler: Optional callable to handle skill invocations.
        """
        self._skills[definition.id] = definition
        if handler is not None:
            self._handlers[definition.id] = handler

    def invoke_skill(self, invocation: SkillInvocation) -> SkillResult:
        """Invoke a registered skill.

        Args:
            invocation: The skill invocation request.

        Returns:
            The result of the skill invocation.

        Raises:
            ValueError: If the skill is not registered.
        """
        if invocation.skill_id not in self._skills:
            raise ValueError(f"Skill not found: {invocation.skill_id}")

        timestamp = self._context.now_iso()
        start_time = self._context.now()

        handler = self._handlers.get(invocation.skill_id)
        if handler is not None:
            try:
                outputs = handler(invocation.inputs)
                duration_ms = (self._context.now() - start_time) * 1000
                return SkillResult(
                    skill_id=invocation.skill_id,
                    outputs=outputs if isinstance(outputs, dict) else {},
                    success=True,
                    duration_ms=duration_ms,
                    timestamp=timestamp,
                )
            except Exception as e:
                duration_ms = (self._context.now() - start_time) * 1000
                return SkillResult(
                    skill_id=invocation.skill_id,
                    success=False,
                    duration_ms=duration_ms,
                    timestamp=timestamp,
                    error=str(e),
                )
        else:
            duration_ms = (self._context.now() - start_time) * 1000
            return SkillResult(
                skill_id=invocation.skill_id,
                outputs={},
                success=True,
                duration_ms=duration_ms,
                timestamp=timestamp,
            )

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        """Get a skill definition by ID.

        Args:
            skill_id: The skill ID to look up.

        Returns:
            The skill definition if found, None otherwise.
        """
        return self._skills.get(skill_id)

    def list_skills(self) -> List[SkillDefinition]:
        """List all registered skills.

        Returns:
            List of all skill definitions.
        """
        return list(self._skills.values())

    @property
    def skill_count(self) -> int:
        """Get the number of registered skills."""
        return len(self._skills)
