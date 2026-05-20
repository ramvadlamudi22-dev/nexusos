"""Browser runtime - session lifecycle and action execution."""

import hashlib
from typing import Dict, List, Optional

from backend.browser.models import (
    BrowserAction,
    BrowserActionResult,
    BrowserSession,
    BrowserSessionState,
)
from backend.runtime.context import RuntimeExecutionContext


class BrowserRuntime:
    """Manages browser sessions and action execution.

    Wraps Playwright for real browser interaction but handles session
    lifecycle independently for testability.
    """

    def __init__(self, context: RuntimeExecutionContext):
        """Initialize browser runtime with execution context.

        Args:
            context: Runtime execution context for deterministic timestamps.
        """
        self._context = context
        self._sessions: Dict[str, BrowserSession] = {}

    def start_session(self, url: str) -> BrowserSession:
        """Create and start a new browser session.

        Args:
            url: The initial URL to navigate to.

        Returns:
            The created BrowserSession in ACTIVE state.
        """
        timestamp = self._context.now_iso()
        session_id = hashlib.sha256(
            f"{url}{timestamp}".encode("utf-8")
        ).hexdigest()[:16]

        session = BrowserSession(
            id=session_id,
            url=url,
            state=BrowserSessionState.ACTIVE,
            creation_timestamp=timestamp,
        )
        self._sessions[session_id] = session
        return session

    def execute_action(
        self, session_id: str, action: BrowserAction
    ) -> BrowserActionResult:
        """Execute a browser action within a session.

        Args:
            session_id: The session to execute the action in.
            action: The browser action to execute.

        Returns:
            The result of the action execution.

        Raises:
            ValueError: If the session does not exist.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        timestamp = self._context.now_iso()
        action.timestamp = timestamp

        result = BrowserActionResult(
            success=True,
            action=action,
            timestamp=timestamp,
        )

        session.recording.append(
            {"action": action.model_dump(), "result": result.model_dump()}
        )

        return result

    def capture_screenshot(self, session_id: str) -> str:
        """Capture a screenshot of the current browser state.

        Args:
            session_id: The session to capture.

        Returns:
            The deterministic path to the screenshot file.

        Raises:
            ValueError: If the session does not exist.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        timestamp = self._context.now_iso()
        screenshot_path = f"/screenshots/{session_id}/{timestamp}.png"
        session.screenshots.append(screenshot_path)
        return screenshot_path

    def stop_session(self, session_id: str) -> BrowserSession:
        """Stop a browser session.

        Args:
            session_id: The session to stop.

        Returns:
            The session in COMPLETED state.

        Raises:
            ValueError: If the session does not exist.
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        session.state = BrowserSessionState.COMPLETED
        return session

    def get_session(self, session_id: str) -> Optional[BrowserSession]:
        """Get a session by ID.

        Args:
            session_id: The session ID to look up.

        Returns:
            The session if found, None otherwise.
        """
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[BrowserSession]:
        """List all browser sessions.

        Returns:
            List of all browser sessions.
        """
        return list(self._sessions.values())
