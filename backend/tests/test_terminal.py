"""Tests for terminal runtime - session management and command execution."""

import pytest

from backend.runtime.context import RuntimeExecutionContext
from backend.terminal.models import TerminalCommand, TerminalSessionState
from backend.terminal.runtime import TerminalRuntime


def make_context(fixed_time: float = 1000000.0) -> RuntimeExecutionContext:
    """Create a context with a fixed time source for deterministic testing."""
    return RuntimeExecutionContext(time_source=lambda: fixed_time)


class TestTerminalSessionLifecycle:
    """Test terminal session creation and state management."""

    def test_create_session_returns_idle_session(self):
        """Creating a session returns a session in IDLE state."""
        ctx = make_context()
        runtime = TerminalRuntime(ctx)

        session = runtime.create_session()

        assert session.state == TerminalSessionState.IDLE
        assert session.id != ""
        assert session.creation_timestamp != ""
        assert session.command_history == []

    def test_get_session_returns_existing(self):
        """Can retrieve a session by its ID."""
        ctx = make_context()
        runtime = TerminalRuntime(ctx)

        session = runtime.create_session()
        found = runtime.get_session(session.id)

        assert found is not None
        assert found.id == session.id

    def test_get_session_returns_none_for_missing(self):
        """Getting a nonexistent session returns None."""
        ctx = make_context()
        runtime = TerminalRuntime(ctx)

        assert runtime.get_session("nonexistent") is None

    def test_close_session_transitions_to_completed(self):
        """Closing a session transitions it to COMPLETED."""
        ctx = make_context()
        runtime = TerminalRuntime(ctx)

        session = runtime.create_session()
        closed = runtime.close_session(session.id)

        assert closed.state == TerminalSessionState.COMPLETED

    def test_close_nonexistent_session_raises(self):
        """Closing a nonexistent session raises ValueError."""
        ctx = make_context()
        runtime = TerminalRuntime(ctx)

        with pytest.raises(ValueError, match="Session not found"):
            runtime.close_session("nonexistent")

    def test_list_sessions(self):
        """Can list all terminal sessions."""
        counter = {"t": 1000000.0}

        def advancing_time():
            counter["t"] += 1.0
            return counter["t"]

        ctx = RuntimeExecutionContext(time_source=advancing_time)
        runtime = TerminalRuntime(ctx)

        runtime.create_session()
        runtime.create_session()

        sessions = runtime.list_sessions()
        assert len(sessions) == 2


class TestTerminalCommandExecution:
    """Test command execution within sessions."""

    def test_execute_simple_command(self):
        """Can execute a simple echo command and capture stdout."""
        ctx = make_context()
        runtime = TerminalRuntime(ctx)

        session = runtime.create_session()
        command = TerminalCommand(command="echo hello")

        result = runtime.execute_command(session.id, command)

        assert result.stdout.strip() == "hello"
        assert result.exit_code == 0
        assert result.duration_ms >= 0

    def test_execute_command_captures_stderr(self):
        """Can capture stderr from a command."""
        ctx = make_context()
        runtime = TerminalRuntime(ctx)

        session = runtime.create_session()
        command = TerminalCommand(command="echo error >&2")

        result = runtime.execute_command(session.id, command)

        assert result.stderr.strip() == "error"

    def test_execute_command_records_history(self):
        """Each executed command is recorded in session history."""
        ctx = make_context()
        runtime = TerminalRuntime(ctx)

        session = runtime.create_session()
        runtime.execute_command(session.id, TerminalCommand(command="echo a"))
        runtime.execute_command(session.id, TerminalCommand(command="echo b"))

        updated = runtime.get_session(session.id)
        assert len(updated.command_history) == 2

    def test_execute_command_nonexistent_session_raises(self):
        """Executing on a nonexistent session raises ValueError."""
        ctx = make_context()
        runtime = TerminalRuntime(ctx)

        with pytest.raises(ValueError, match="Session not found"):
            runtime.execute_command("nonexistent", TerminalCommand(command="echo hi"))

    def test_execute_command_with_timeout(self):
        """Commands exceeding timeout produce error result."""
        ctx = make_context()
        runtime = TerminalRuntime(ctx)

        session = runtime.create_session()
        command = TerminalCommand(command="sleep 10", timeout_seconds=1)

        result = runtime.execute_command(session.id, command)

        assert result.exit_code == -1
        assert "timed out" in result.stderr.lower()

    def test_session_returns_to_idle_after_command(self):
        """Session returns to IDLE state after successful command."""
        ctx = make_context()
        runtime = TerminalRuntime(ctx)

        session = runtime.create_session()
        runtime.execute_command(session.id, TerminalCommand(command="echo ok"))

        updated = runtime.get_session(session.id)
        assert updated.state == TerminalSessionState.IDLE

    def test_session_goes_to_error_on_timeout(self):
        """Session transitions to ERROR on timeout."""
        ctx = make_context()
        runtime = TerminalRuntime(ctx)

        session = runtime.create_session()
        runtime.execute_command(
            session.id, TerminalCommand(command="sleep 10", timeout_seconds=1)
        )

        updated = runtime.get_session(session.id)
        assert updated.state == TerminalSessionState.ERROR

    def test_execute_command_with_exit_code(self):
        """Non-zero exit codes are captured."""
        ctx = make_context()
        runtime = TerminalRuntime(ctx)

        session = runtime.create_session()
        result = runtime.execute_command(
            session.id, TerminalCommand(command="exit 42")
        )

        assert result.exit_code == 42
