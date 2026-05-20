"""Tests for execution replay manager."""

from backend.replay.execution import ExecutionReplayManager
from backend.replay.recorder import ReplayRecorder
from backend.runtime.context import RuntimeExecutionContext


def make_context(fixed_time: float = 1000000.0) -> RuntimeExecutionContext:
    """Create a context with a fixed time source for deterministic testing."""
    return RuntimeExecutionContext(time_source=lambda: fixed_time)


class TestBrowserSessionReplay:
    """Test browser session recording and replay."""

    def test_record_and_replay_browser_session(self):
        """Can record and replay a browser session."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)
        manager = ExecutionReplayManager(ctx, recorder)

        actions = [
            {"action": "NAVIGATE", "target": "https://example.com"},
            {"action": "CLICK", "target": "#btn"},
        ]

        manager.record_browser_session("sess-1", actions)
        replayed = manager.replay_browser_session("sess-1")

        assert replayed == actions

    def test_replay_nonexistent_browser_session(self):
        """Replaying a nonexistent session returns None."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)
        manager = ExecutionReplayManager(ctx, recorder)

        assert manager.replay_browser_session("nonexistent") is None


class TestTerminalSessionReplay:
    """Test terminal session recording and replay."""

    def test_record_and_replay_terminal_session(self):
        """Can record and replay a terminal session."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)
        manager = ExecutionReplayManager(ctx, recorder)

        commands = [
            {"command": "echo hello", "exit_code": 0, "stdout": "hello\n"},
            {"command": "ls", "exit_code": 0, "stdout": "file.txt\n"},
        ]

        manager.record_terminal_session("sess-1", commands)
        replayed = manager.replay_terminal_session("sess-1")

        assert replayed == commands

    def test_replay_nonexistent_terminal_session(self):
        """Replaying a nonexistent session returns None."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)
        manager = ExecutionReplayManager(ctx, recorder)

        assert manager.replay_terminal_session("nonexistent") is None


class TestWorkflowExecutionReplay:
    """Test workflow execution recording and replay."""

    def test_record_and_replay_workflow(self):
        """Can record and replay a workflow execution."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)
        manager = ExecutionReplayManager(ctx, recorder)

        steps = [
            {"step_id": "step-1", "status": "success", "outputs": {}},
            {"step_id": "step-2", "status": "success", "outputs": {"data": 42}},
        ]

        manager.record_workflow_execution("exec-1", steps)
        replayed = manager.replay_workflow_execution("exec-1")

        assert replayed == steps

    def test_replay_nonexistent_workflow(self):
        """Replaying a nonexistent workflow returns None."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)
        manager = ExecutionReplayManager(ctx, recorder)

        assert manager.replay_workflow_execution("nonexistent") is None


class TestReplayVerification:
    """Test replay verification."""

    def test_verify_matching_replay(self):
        """Matching original and replayed data returns True."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)
        manager = ExecutionReplayManager(ctx, recorder)

        original = [{"action": "CLICK", "target": "#btn"}]
        replayed = [{"action": "CLICK", "target": "#btn"}]

        assert manager.verify_replay(original, replayed) is True

    def test_verify_mismatched_replay(self):
        """Mismatched data returns False."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)
        manager = ExecutionReplayManager(ctx, recorder)

        original = [{"action": "CLICK", "target": "#btn"}]
        replayed = [{"action": "CLICK", "target": "#other"}]

        assert manager.verify_replay(original, replayed) is False

    def test_verify_different_lengths(self):
        """Different lengths returns False."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)
        manager = ExecutionReplayManager(ctx, recorder)

        original = [{"action": "CLICK"}, {"action": "TYPE"}]
        replayed = [{"action": "CLICK"}]

        assert manager.verify_replay(original, replayed) is False

    def test_verify_empty_lists(self):
        """Empty lists match."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)
        manager = ExecutionReplayManager(ctx, recorder)

        assert manager.verify_replay([], []) is True

    def test_recording_creates_replay_record(self):
        """Recording operations creates entries in the replay recorder."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)
        manager = ExecutionReplayManager(ctx, recorder)

        manager.record_browser_session("s1", [{"action": "NAVIGATE"}])
        manager.record_terminal_session("s2", [{"command": "ls"}])
        manager.record_workflow_execution("e1", [{"step_id": "s1"}])

        assert recorder.record_count == 3
