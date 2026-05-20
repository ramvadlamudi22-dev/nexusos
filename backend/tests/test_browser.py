"""Tests for browser runtime - session lifecycle and action execution."""

import pytest

from backend.browser.models import (
    BrowserAction,
    BrowserActionType,
    BrowserSessionState,
)
from backend.browser.runtime import BrowserRuntime
from backend.runtime.context import RuntimeExecutionContext


def make_context(fixed_time: float = 1000000.0) -> RuntimeExecutionContext:
    """Create a context with a fixed time source for deterministic testing."""
    return RuntimeExecutionContext(time_source=lambda: fixed_time)


class TestBrowserSessionLifecycle:
    """Test browser session creation and state management."""

    def test_start_session_creates_active_session(self):
        """Starting a session returns an ACTIVE session."""
        ctx = make_context()
        runtime = BrowserRuntime(ctx)

        session = runtime.start_session("https://example.com")

        assert session.state == BrowserSessionState.ACTIVE
        assert session.url == "https://example.com"
        assert session.id != ""
        assert session.creation_timestamp != ""

    def test_start_session_deterministic_id(self):
        """Same URL and time produce the same session ID."""
        ctx = make_context(fixed_time=1000000.0)
        runtime1 = BrowserRuntime(ctx)
        runtime2 = BrowserRuntime(ctx)

        session1 = runtime1.start_session("https://example.com")
        session2 = runtime2.start_session("https://example.com")

        assert session1.id == session2.id

    def test_get_session_returns_existing(self):
        """Can retrieve a session by its ID."""
        ctx = make_context()
        runtime = BrowserRuntime(ctx)

        session = runtime.start_session("https://example.com")
        found = runtime.get_session(session.id)

        assert found is not None
        assert found.id == session.id

    def test_get_session_returns_none_for_missing(self):
        """Getting a nonexistent session returns None."""
        ctx = make_context()
        runtime = BrowserRuntime(ctx)

        assert runtime.get_session("nonexistent") is None

    def test_stop_session_transitions_to_completed(self):
        """Stopping a session transitions it to COMPLETED."""
        ctx = make_context()
        runtime = BrowserRuntime(ctx)

        session = runtime.start_session("https://example.com")
        stopped = runtime.stop_session(session.id)

        assert stopped.state == BrowserSessionState.COMPLETED

    def test_stop_nonexistent_session_raises(self):
        """Stopping a nonexistent session raises ValueError."""
        ctx = make_context()
        runtime = BrowserRuntime(ctx)

        with pytest.raises(ValueError, match="Session not found"):
            runtime.stop_session("nonexistent")

    def test_list_sessions(self):
        """Can list all browser sessions."""
        ctx = make_context()
        runtime = BrowserRuntime(ctx)

        runtime.start_session("https://a.com")
        runtime.start_session("https://b.com")

        sessions = runtime.list_sessions()
        assert len(sessions) == 2


class TestBrowserActions:
    """Test browser action execution."""

    def test_execute_action_success(self):
        """Executing a valid action returns a successful result."""
        ctx = make_context()
        runtime = BrowserRuntime(ctx)

        session = runtime.start_session("https://example.com")
        action = BrowserAction(
            action_type=BrowserActionType.NAVIGATE,
            target="https://example.com/page",
        )

        result = runtime.execute_action(session.id, action)

        assert result.success is True
        assert result.action.action_type == BrowserActionType.NAVIGATE
        assert result.timestamp != ""

    def test_execute_action_records_to_session(self):
        """Each executed action is recorded in the session recording list."""
        ctx = make_context()
        runtime = BrowserRuntime(ctx)

        session = runtime.start_session("https://example.com")
        action = BrowserAction(
            action_type=BrowserActionType.CLICK,
            target="#button",
        )

        runtime.execute_action(session.id, action)

        updated_session = runtime.get_session(session.id)
        assert len(updated_session.recording) == 1
        assert updated_session.recording[0]["action"]["action_type"] == "CLICK"

    def test_execute_action_nonexistent_session_raises(self):
        """Executing an action on a nonexistent session raises ValueError."""
        ctx = make_context()
        runtime = BrowserRuntime(ctx)

        action = BrowserAction(
            action_type=BrowserActionType.NAVIGATE,
            target="https://example.com",
        )

        with pytest.raises(ValueError, match="Session not found"):
            runtime.execute_action("nonexistent", action)

    def test_multiple_actions_recorded_in_order(self):
        """Multiple actions are recorded sequentially."""
        ctx = make_context()
        runtime = BrowserRuntime(ctx)

        session = runtime.start_session("https://example.com")
        actions = [
            BrowserAction(action_type=BrowserActionType.NAVIGATE, target="/page1"),
            BrowserAction(action_type=BrowserActionType.CLICK, target="#btn"),
            BrowserAction(action_type=BrowserActionType.TYPE, target="#input", value="hello"),
        ]

        for action in actions:
            runtime.execute_action(session.id, action)

        updated = runtime.get_session(session.id)
        assert len(updated.recording) == 3


class TestBrowserScreenshots:
    """Test screenshot capture."""

    def test_capture_screenshot_returns_path(self):
        """Capturing a screenshot returns a path string."""
        ctx = make_context()
        runtime = BrowserRuntime(ctx)

        session = runtime.start_session("https://example.com")
        path = runtime.capture_screenshot(session.id)

        assert path.startswith("/screenshots/")
        assert session.id in path
        assert path.endswith(".png")

    def test_capture_screenshot_appends_to_session(self):
        """Screenshots are recorded in the session screenshots list."""
        ctx = make_context()
        runtime = BrowserRuntime(ctx)

        session = runtime.start_session("https://example.com")
        runtime.capture_screenshot(session.id)
        runtime.capture_screenshot(session.id)

        updated = runtime.get_session(session.id)
        assert len(updated.screenshots) == 2

    def test_capture_screenshot_nonexistent_session_raises(self):
        """Capturing a screenshot for a nonexistent session raises ValueError."""
        ctx = make_context()
        runtime = BrowserRuntime(ctx)

        with pytest.raises(ValueError, match="Session not found"):
            runtime.capture_screenshot("nonexistent")
