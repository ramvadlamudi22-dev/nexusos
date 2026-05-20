"""Tests for execution telemetry collector."""

from backend.runtime.context import RuntimeExecutionContext
from backend.telemetry.collector import TelemetryCollector
from backend.telemetry.execution import ExecutionTelemetryCollector


def make_context(fixed_time: float = 1000000.0) -> RuntimeExecutionContext:
    """Create a context with a fixed time source for deterministic testing."""
    return RuntimeExecutionContext(time_source=lambda: fixed_time)


class TestBrowserTelemetry:
    """Test browser action telemetry recording."""

    def test_record_browser_trace_increments_counter(self):
        """Recording a browser trace increments the browser counter."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)
        exec_telemetry = ExecutionTelemetryCollector(ctx, collector)

        exec_telemetry.record_browser_trace(
            session_id="sess-1",
            action={"action_type": "NAVIGATE", "target": "https://example.com"},
            result={"success": True},
        )

        metrics = exec_telemetry.get_execution_metrics()
        assert metrics["counters"]["browser_actions"] == 1

    def test_record_browser_error_increments_error_counter(self):
        """Browser errors increment the error counter."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)
        exec_telemetry = ExecutionTelemetryCollector(ctx, collector)

        exec_telemetry.record_browser_trace(
            session_id="sess-1",
            action={"action_type": "CLICK"},
            result={"success": False},
        )

        metrics = exec_telemetry.get_execution_metrics()
        assert metrics["errors"]["browser_errors"] == 1


class TestTerminalTelemetry:
    """Test terminal command telemetry recording."""

    def test_record_terminal_trace_increments_counter(self):
        """Recording a terminal trace increments the terminal counter."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)
        exec_telemetry = ExecutionTelemetryCollector(ctx, collector)

        exec_telemetry.record_terminal_trace(
            session_id="sess-1",
            command="echo hello",
            result={"exit_code": 0},
        )

        metrics = exec_telemetry.get_execution_metrics()
        assert metrics["counters"]["terminal_commands"] == 1

    def test_record_terminal_error(self):
        """Non-zero exit codes increment terminal error counter."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)
        exec_telemetry = ExecutionTelemetryCollector(ctx, collector)

        exec_telemetry.record_terminal_trace(
            session_id="sess-1",
            command="false",
            result={"exit_code": 1},
        )

        metrics = exec_telemetry.get_execution_metrics()
        assert metrics["errors"]["terminal_errors"] == 1


class TestWorkflowTelemetry:
    """Test workflow step telemetry recording."""

    def test_record_workflow_trace_increments_counter(self):
        """Recording a workflow trace increments the workflow counter."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)
        exec_telemetry = ExecutionTelemetryCollector(ctx, collector)

        exec_telemetry.record_workflow_trace(
            execution_id="exec-1",
            step_id="step-1",
            result={"status": "success"},
        )

        metrics = exec_telemetry.get_execution_metrics()
        assert metrics["counters"]["workflow_executions"] == 1

    def test_record_workflow_failure(self):
        """Failed workflow steps increment error counter."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)
        exec_telemetry = ExecutionTelemetryCollector(ctx, collector)

        exec_telemetry.record_workflow_trace(
            execution_id="exec-1",
            step_id="step-1",
            result={"status": "failed"},
        )

        metrics = exec_telemetry.get_execution_metrics()
        assert metrics["errors"]["workflow_errors"] == 1


class TestSkillTelemetry:
    """Test skill invocation telemetry recording."""

    def test_record_skill_trace_increments_counter(self):
        """Recording a skill trace increments the skill counter."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)
        exec_telemetry = ExecutionTelemetryCollector(ctx, collector)

        exec_telemetry.record_skill_trace(
            skill_id="math-add",
            invocation={"inputs": {"a": 1, "b": 2}},
            result={"success": True},
        )

        metrics = exec_telemetry.get_execution_metrics()
        assert metrics["counters"]["skill_invocations"] == 1

    def test_record_skill_failure(self):
        """Failed skill invocations increment error counter."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)
        exec_telemetry = ExecutionTelemetryCollector(ctx, collector)

        exec_telemetry.record_skill_trace(
            skill_id="bad-skill",
            invocation={"inputs": {}},
            result={"success": False},
        )

        metrics = exec_telemetry.get_execution_metrics()
        assert metrics["errors"]["skill_errors"] == 1


class TestAggregatedMetrics:
    """Test aggregated execution metrics and health."""

    def test_total_operations(self):
        """Total operations sums all counters."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)
        exec_telemetry = ExecutionTelemetryCollector(ctx, collector)

        exec_telemetry.record_browser_trace("s1", {}, {"success": True})
        exec_telemetry.record_terminal_trace("s2", "ls", {"exit_code": 0})
        exec_telemetry.record_skill_trace("sk1", {}, {"success": True})

        metrics = exec_telemetry.get_execution_metrics()
        assert metrics["total_operations"] == 3

    def test_health_idle_when_no_operations(self):
        """Health shows idle when no operations recorded."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)
        exec_telemetry = ExecutionTelemetryCollector(ctx, collector)

        health = exec_telemetry.get_execution_health()
        assert health["browser"]["status"] == "idle"
        assert health["terminal"]["status"] == "idle"

    def test_health_healthy_when_no_errors(self):
        """Health shows healthy when operations succeed."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)
        exec_telemetry = ExecutionTelemetryCollector(ctx, collector)

        exec_telemetry.record_browser_trace("s1", {}, {"success": True})

        health = exec_telemetry.get_execution_health()
        assert health["browser"]["status"] == "healthy"

    def test_health_degraded_when_some_errors(self):
        """Health shows degraded when error rate is below 50%."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)
        exec_telemetry = ExecutionTelemetryCollector(ctx, collector)

        exec_telemetry.record_terminal_trace("s1", "ls", {"exit_code": 0})
        exec_telemetry.record_terminal_trace("s1", "ls", {"exit_code": 0})
        exec_telemetry.record_terminal_trace("s1", "bad", {"exit_code": 1})

        health = exec_telemetry.get_execution_health()
        assert health["terminal"]["status"] == "degraded"

    def test_health_unhealthy_when_many_errors(self):
        """Health shows unhealthy when error rate is 50% or above."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)
        exec_telemetry = ExecutionTelemetryCollector(ctx, collector)

        exec_telemetry.record_skill_trace("s1", {}, {"success": False})
        exec_telemetry.record_skill_trace("s2", {}, {"success": False})

        health = exec_telemetry.get_execution_health()
        assert health["skill"]["status"] == "unhealthy"
