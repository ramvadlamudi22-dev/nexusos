"""Execution replay manager - records and replays execution sessions."""

from typing import Any, Dict, List, Optional

from backend.replay.recorder import ReplayRecorder
from backend.runtime.context import RuntimeExecutionContext


class ExecutionReplayManager:
    """Manages recording and replay of execution sessions.

    Records browser sessions, terminal sessions, and workflow executions
    for deterministic replay and verification.
    """

    def __init__(
        self,
        context: RuntimeExecutionContext,
        replay_recorder: ReplayRecorder,
    ):
        """Initialize the execution replay manager.

        Args:
            context: Runtime execution context.
            replay_recorder: The underlying replay recorder.
        """
        self._context = context
        self._recorder = replay_recorder
        self._browser_sessions: Dict[str, List[Dict[str, Any]]] = {}
        self._terminal_sessions: Dict[str, List[Dict[str, Any]]] = {}
        self._workflow_executions: Dict[str, List[Dict[str, Any]]] = {}

    def record_browser_session(
        self, session_id: str, actions_and_results: List[Dict[str, Any]]
    ) -> None:
        """Record a browser session for replay.

        Appends to existing records if the session already has data.

        Args:
            session_id: The browser session ID.
            actions_and_results: List of action/result pairs.
        """
        if session_id not in self._browser_sessions:
            self._browser_sessions[session_id] = []
        self._browser_sessions[session_id].extend(actions_and_results)
        self._recorder.record(
            operation="browser_session",
            inputs={"session_id": session_id},
            outputs={"actions_count": len(self._browser_sessions[session_id])},
        )

    def record_terminal_session(
        self, session_id: str, commands_and_results: List[Dict[str, Any]]
    ) -> None:
        """Record a terminal session for replay.

        Appends to existing records if the session already has data.

        Args:
            session_id: The terminal session ID.
            commands_and_results: List of command/result pairs.
        """
        if session_id not in self._terminal_sessions:
            self._terminal_sessions[session_id] = []
        self._terminal_sessions[session_id].extend(commands_and_results)
        self._recorder.record(
            operation="terminal_session",
            inputs={"session_id": session_id},
            outputs={"commands_count": len(self._terminal_sessions[session_id])},
        )

    def record_workflow_execution(
        self, execution_id: str, steps_and_results: List[Dict[str, Any]]
    ) -> None:
        """Record a workflow execution for replay.

        Appends to existing records if the execution already has data.

        Args:
            execution_id: The workflow execution ID.
            steps_and_results: List of step/result pairs.
        """
        if execution_id not in self._workflow_executions:
            self._workflow_executions[execution_id] = []
        self._workflow_executions[execution_id].extend(steps_and_results)
        self._recorder.record(
            operation="workflow_execution",
            inputs={"execution_id": execution_id},
            outputs={"steps_count": len(self._workflow_executions[execution_id])},
        )

    def replay_browser_session(
        self, session_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Replay a recorded browser session.

        Args:
            session_id: The browser session ID to replay.

        Returns:
            The recorded actions and results, or None if not found.
        """
        return self._browser_sessions.get(session_id)

    def replay_terminal_session(
        self, session_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Replay a recorded terminal session.

        Args:
            session_id: The terminal session ID to replay.

        Returns:
            The recorded commands and results, or None if not found.
        """
        return self._terminal_sessions.get(session_id)

    def replay_workflow_execution(
        self, execution_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Replay a recorded workflow execution.

        Args:
            execution_id: The workflow execution ID to replay.

        Returns:
            The recorded steps and results, or None if not found.
        """
        return self._workflow_executions.get(execution_id)

    def verify_replay(
        self, original: List[Dict[str, Any]], replayed: List[Dict[str, Any]]
    ) -> bool:
        """Verify that a replay matches the original recording.

        Args:
            original: The original recorded actions/commands/steps.
            replayed: The replayed actions/commands/steps.

        Returns:
            True if they match, False otherwise.
        """
        if len(original) != len(replayed):
            return False

        for orig, rep in zip(original, replayed):
            if orig != rep:
                return False

        return True
