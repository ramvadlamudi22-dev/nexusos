"""Terminal runtime - sandboxed subprocess execution with session management."""

import hashlib
import subprocess
from typing import Dict, List, Optional

from backend.runtime.context import RuntimeExecutionContext
from backend.terminal.models import (
    TerminalCommand,
    TerminalResult,
    TerminalSession,
    TerminalSessionState,
)


class TerminalRuntime:
    """Manages terminal sessions and command execution.

    Executes commands via subprocess.run with timeout enforcement
    and captures stdout/stderr for replay.
    """

    def __init__(self, context: RuntimeExecutionContext):
        """Initialize terminal runtime with execution context.

        Args:
            context: Runtime execution context for deterministic timestamps.
        """
        self._context = context
        self._sessions: Dict[str, TerminalSession] = {}

    def create_session(self) -> TerminalSession:
        """Create a new terminal session.

        Returns:
            The created TerminalSession in IDLE state.
        """
        timestamp = self._context.now_iso()
        session_id = hashlib.sha256(
            f"terminal{timestamp}".encode("utf-8")
        ).hexdigest()[:16]

        session = TerminalSession(
            id=session_id,
            state=TerminalSessionState.IDLE,
            creation_timestamp=timestamp,
        )
        self._sessions[session_id] = session
        return session

    def execute_command(
        self, session_id: str, command: TerminalCommand
    ) -> TerminalResult:
        """Execute a command within a terminal session.

        Args:
            session_id: The session to execute the command in.
            command: The terminal command to execute.

        Returns:
            The result of command execution.

        Raises:
            ValueError: If the session does not exist.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        session.state = TerminalSessionState.EXECUTING
        timestamp = self._context.now_iso()

        start_time = self._context.now()
        try:
            proc = subprocess.run(
                command.command,
                shell=True,
                cwd=command.working_dir,
                timeout=command.timeout_seconds,
                capture_output=True,
                text=True,
                env=command.environment if command.environment else None,
            )
            duration_ms = (self._context.now() - start_time) * 1000

            result = TerminalResult(
                command=command.command,
                stdout=proc.stdout,
                stderr=proc.stderr,
                exit_code=proc.returncode,
                duration_ms=duration_ms,
                timestamp=timestamp,
            )
        except subprocess.TimeoutExpired:
            duration_ms = (self._context.now() - start_time) * 1000
            result = TerminalResult(
                command=command.command,
                stdout="",
                stderr="Command timed out",
                exit_code=-1,
                duration_ms=duration_ms,
                timestamp=timestamp,
            )
            session.state = TerminalSessionState.ERROR
            session.command_history.append(result)
            return result

        session.state = TerminalSessionState.IDLE
        session.command_history.append(result)
        return result

    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        """Get a session by ID.

        Args:
            session_id: The session ID to look up.

        Returns:
            The session if found, None otherwise.
        """
        return self._sessions.get(session_id)

    def close_session(self, session_id: str) -> TerminalSession:
        """Close a terminal session.

        Args:
            session_id: The session to close.

        Returns:
            The session in COMPLETED state.

        Raises:
            ValueError: If the session does not exist.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        session.state = TerminalSessionState.COMPLETED
        return session

    def list_sessions(self) -> List[TerminalSession]:
        """List all terminal sessions.

        Returns:
            List of all terminal sessions.
        """
        return list(self._sessions.values())
