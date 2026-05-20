"""Tests for skills runtime - registration, invocation, and listing."""

import pytest

from backend.runtime.context import RuntimeExecutionContext
from backend.skills.models import SkillDefinition, SkillInvocation
from backend.skills.runtime import SkillRuntime


def make_context(fixed_time: float = 1000000.0) -> RuntimeExecutionContext:
    """Create a context with a fixed time source for deterministic testing."""
    return RuntimeExecutionContext(time_source=lambda: fixed_time)


class TestSkillRegistration:
    """Test skill registration and listing."""

    def test_register_skill(self):
        """Can register a skill definition."""
        ctx = make_context()
        runtime = SkillRuntime(ctx)

        definition = SkillDefinition(
            id="math-add",
            name="Math Add",
            description="Adds two numbers",
            input_schema={"a": "number", "b": "number"},
            output_schema={"result": "number"},
        )

        runtime.register_skill(definition)

        assert runtime.skill_count == 1

    def test_get_registered_skill(self):
        """Can retrieve a registered skill by ID."""
        ctx = make_context()
        runtime = SkillRuntime(ctx)

        definition = SkillDefinition(id="test-skill", name="Test")
        runtime.register_skill(definition)

        found = runtime.get_skill("test-skill")
        assert found is not None
        assert found.id == "test-skill"

    def test_get_nonexistent_skill_returns_none(self):
        """Getting a nonexistent skill returns None."""
        ctx = make_context()
        runtime = SkillRuntime(ctx)

        assert runtime.get_skill("nonexistent") is None

    def test_list_skills(self):
        """Can list all registered skills."""
        ctx = make_context()
        runtime = SkillRuntime(ctx)

        runtime.register_skill(SkillDefinition(id="s1", name="Skill 1"))
        runtime.register_skill(SkillDefinition(id="s2", name="Skill 2"))

        skills = runtime.list_skills()
        assert len(skills) == 2

    def test_skill_count(self):
        """skill_count reflects number of registered skills."""
        ctx = make_context()
        runtime = SkillRuntime(ctx)

        assert runtime.skill_count == 0
        runtime.register_skill(SkillDefinition(id="s1", name="S1"))
        assert runtime.skill_count == 1


class TestSkillInvocation:
    """Test skill invocation."""

    def test_invoke_skill_without_handler(self):
        """Invoking a skill without a handler returns success with empty outputs."""
        ctx = make_context()
        runtime = SkillRuntime(ctx)

        runtime.register_skill(SkillDefinition(id="noop", name="No-op"))
        invocation = SkillInvocation(skill_id="noop", inputs={})

        result = runtime.invoke_skill(invocation)

        assert result.success is True
        assert result.skill_id == "noop"
        assert result.timestamp != ""

    def test_invoke_skill_with_handler(self):
        """Invoking a skill with a handler executes the handler."""
        ctx = make_context()
        runtime = SkillRuntime(ctx)

        def add_handler(inputs):
            return {"result": inputs["a"] + inputs["b"]}

        runtime.register_skill(
            SkillDefinition(id="add", name="Add"),
            handler=add_handler,
        )

        result = runtime.invoke_skill(
            SkillInvocation(skill_id="add", inputs={"a": 2, "b": 3})
        )

        assert result.success is True
        assert result.outputs == {"result": 5}

    def test_invoke_skill_handler_error(self):
        """A handler raising an exception returns a failed result."""
        ctx = make_context()
        runtime = SkillRuntime(ctx)

        def failing_handler(inputs):
            raise RuntimeError("Something went wrong")

        runtime.register_skill(
            SkillDefinition(id="fail", name="Fail"),
            handler=failing_handler,
        )

        result = runtime.invoke_skill(
            SkillInvocation(skill_id="fail", inputs={})
        )

        assert result.success is False
        assert "Something went wrong" in result.error

    def test_invoke_nonexistent_skill_raises(self):
        """Invoking a nonexistent skill raises ValueError."""
        ctx = make_context()
        runtime = SkillRuntime(ctx)

        with pytest.raises(ValueError, match="Skill not found"):
            runtime.invoke_skill(SkillInvocation(skill_id="missing", inputs={}))

    def test_invoke_skill_records_duration(self):
        """Skill invocation records duration in milliseconds."""
        ctx = make_context()
        runtime = SkillRuntime(ctx)

        runtime.register_skill(SkillDefinition(id="timed", name="Timed"))
        result = runtime.invoke_skill(
            SkillInvocation(skill_id="timed", inputs={})
        )

        assert result.duration_ms >= 0
