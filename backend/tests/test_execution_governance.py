"""Tests for execution governance validator."""

from backend.governance.engine import GovernanceEngine
from backend.governance.execution import ExecutionGovernanceValidator
from backend.runtime.context import RuntimeExecutionContext


def make_context(fixed_time: float = 1000000.0) -> RuntimeExecutionContext:
    """Create a context with a fixed time source for deterministic testing."""
    return RuntimeExecutionContext(time_source=lambda: fixed_time)


class TestBrowserActionValidation:
    """Test browser action governance validation."""

    def test_allows_normal_url(self):
        """Normal HTTPS URLs are permitted."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_browser_action(
            {"target": "https://example.com"}
        )

        assert result.permitted is True

    def test_blocks_file_scheme(self):
        """file:// URLs are blocked."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_browser_action(
            {"target": "file:///etc/passwd"}
        )

        assert result.permitted is False
        assert "file://" in result.reason

    def test_blocks_javascript_scheme(self):
        """javascript: URLs are blocked."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_browser_action(
            {"target": "javascript:alert(1)"}
        )

        assert result.permitted is False
        assert "javascript:" in result.reason

    def test_allows_empty_target(self):
        """Empty target is permitted (action may be non-navigation)."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_browser_action({"target": ""})

        assert result.permitted is True

    def test_blocks_case_insensitive(self):
        """URL scheme check is case-insensitive."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_browser_action(
            {"target": "FILE:///etc/shadow"}
        )

        assert result.permitted is False


class TestTerminalCommandValidation:
    """Test terminal command governance validation."""

    def test_allows_safe_command(self):
        """Safe commands are permitted."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_terminal_command("echo hello")

        assert result.permitted is True

    def test_blocks_rm_rf_root(self):
        """rm -rf / is blocked."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_terminal_command("rm -rf /")

        assert result.permitted is False
        assert "rm -rf /" in result.reason

    def test_blocks_shutdown(self):
        """shutdown command is blocked."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_terminal_command("sudo shutdown -h now")

        assert result.permitted is False

    def test_blocks_reboot(self):
        """reboot command is blocked."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_terminal_command("reboot")

        assert result.permitted is False

    def test_blocks_mkfs(self):
        """mkfs command is blocked."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_terminal_command("mkfs.ext4 /dev/sda1")

        assert result.permitted is False

    def test_allows_rm_in_directory(self):
        """rm on a specific file/directory is permitted."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_terminal_command("rm -rf /tmp/test")

        assert result.permitted is True


class TestWorkflowValidation:
    """Test workflow governance validation."""

    def test_allows_valid_workflow(self):
        """Valid workflows are permitted."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_workflow_execution(
            {
                "steps": [
                    {"step_type": "TERMINAL", "id": "s1"},
                    {"step_type": "BROWSER", "id": "s2"},
                ]
            }
        )

        assert result.permitted is True

    def test_blocks_too_many_steps(self):
        """Workflows exceeding max step count are blocked."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        steps = [{"step_type": "TERMINAL", "id": f"s{i}"} for i in range(101)]
        result = validator.validate_workflow_execution({"steps": steps})

        assert result.permitted is False
        assert "maximum step count" in result.reason

    def test_blocks_invalid_step_type(self):
        """Invalid step types are blocked."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_workflow_execution(
            {"steps": [{"step_type": "INVALID_TYPE", "id": "s1"}]}
        )

        assert result.permitted is False
        assert "Invalid step type" in result.reason

    def test_allows_empty_workflow(self):
        """Empty workflows are permitted."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_workflow_execution({"steps": []})

        assert result.permitted is True


class TestSkillInvocationValidation:
    """Test skill invocation governance validation."""

    def test_allows_registered_skill(self):
        """Registered skills are permitted."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_skill_invocation(
            {"skill_id": "math-add"},
            registered_skills=["math-add", "text-transform"],
        )

        assert result.permitted is True

    def test_blocks_unregistered_skill(self):
        """Unregistered skills are blocked."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)
        validator = ExecutionGovernanceValidator(ctx, engine)

        result = validator.validate_skill_invocation(
            {"skill_id": "unknown-skill"},
            registered_skills=["math-add"],
        )

        assert result.permitted is False
        assert "not registered" in result.reason
