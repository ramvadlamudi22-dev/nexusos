"""Execution telemetry collector - records execution traces and metrics."""

from typing import Any, Dict

from backend.runtime.context import RuntimeExecutionContext
from backend.telemetry.collector import TelemetryCollector


class ExecutionTelemetryCollector:
    """Collects telemetry specifically for execution runtime operations.

    Records traces for browser, terminal, workflow, and skill executions.
    Provides aggregated metrics and health information per runtime.
    """

    def __init__(
        self,
        context: RuntimeExecutionContext,
        telemetry_collector: TelemetryCollector,
    ):
        """Initialize the execution telemetry collector.

        Args:
            context: Runtime execution context.
            telemetry_collector: The underlying telemetry collector.
        """
        self._context = context
        self._collector = telemetry_collector
        self._counters: Dict[str, int] = {
            "browser_actions": 0,
            "terminal_commands": 0,
            "workflow_executions": 0,
            "skill_invocations": 0,
        }
        self._errors: Dict[str, int] = {
            "browser_errors": 0,
            "terminal_errors": 0,
            "workflow_errors": 0,
            "skill_errors": 0,
        }

    def record_browser_trace(
        self, session_id: str, action: Dict[str, Any], result: Dict[str, Any]
    ) -> None:
        """Record a browser action trace.

        Args:
            session_id: The browser session ID.
            action: The action that was executed.
            result: The result of the action.
        """
        self._counters["browser_actions"] += 1
        if not result.get("success", True):
            self._errors["browser_errors"] += 1

        self._collector.start_trace(
            operation="browser_action",
            metadata={
                "session_id": session_id,
                "action_type": action.get("action_type", ""),
            },
        )
        self._collector.increment_counter("browser_actions")

    def record_terminal_trace(
        self, session_id: str, command: str, result: Dict[str, Any]
    ) -> None:
        """Record a terminal command trace.

        Args:
            session_id: The terminal session ID.
            command: The command that was executed.
            result: The result of the command.
        """
        self._counters["terminal_commands"] += 1
        if result.get("exit_code", 0) != 0:
            self._errors["terminal_errors"] += 1

        self._collector.start_trace(
            operation="terminal_command",
            metadata={"session_id": session_id, "command": command},
        )
        self._collector.increment_counter("terminal_commands")

    def record_workflow_trace(
        self, execution_id: str, step_id: str, result: Dict[str, Any]
    ) -> None:
        """Record a workflow step trace.

        Args:
            execution_id: The workflow execution ID.
            step_id: The step that was executed.
            result: The result of the step.
        """
        self._counters["workflow_executions"] += 1
        if result.get("status") == "failed":
            self._errors["workflow_errors"] += 1

        self._collector.start_trace(
            operation="workflow_step",
            metadata={"execution_id": execution_id, "step_id": step_id},
        )
        self._collector.increment_counter("workflow_executions")

    def record_skill_trace(
        self, skill_id: str, invocation: Dict[str, Any], result: Dict[str, Any]
    ) -> None:
        """Record a skill invocation trace.

        Args:
            skill_id: The skill that was invoked.
            invocation: The invocation parameters.
            result: The result of the invocation.
        """
        self._counters["skill_invocations"] += 1
        if not result.get("success", True):
            self._errors["skill_errors"] += 1

        self._collector.start_trace(
            operation="skill_invocation",
            metadata={"skill_id": skill_id},
        )
        self._collector.increment_counter("skill_invocations")

    def get_execution_metrics(self) -> Dict[str, Any]:
        """Get execution metrics with counters per runtime.

        Returns:
            Dictionary with counters for each runtime type.
        """
        return {
            "counters": dict(self._counters),
            "errors": dict(self._errors),
            "total_operations": sum(self._counters.values()),
            "total_errors": sum(self._errors.values()),
        }

    def get_execution_health(self) -> Dict[str, Any]:
        """Get health status per runtime.

        Returns:
            Dictionary with health status for each runtime.
        """
        health = {}
        runtime_pairs = [
            ("browser", "browser_actions", "browser_errors"),
            ("terminal", "terminal_commands", "terminal_errors"),
            ("workflow", "workflow_executions", "workflow_errors"),
            ("skill", "skill_invocations", "skill_errors"),
        ]

        for runtime, counter_key, error_key in runtime_pairs:
            total = self._counters[counter_key]
            errors = self._errors[error_key]
            if total == 0:
                status = "idle"
            elif errors == 0:
                status = "healthy"
            elif errors / total < 0.5:
                status = "degraded"
            else:
                status = "unhealthy"

            health[runtime] = {
                "status": status,
                "total_operations": total,
                "errors": errors,
            }

        return health
