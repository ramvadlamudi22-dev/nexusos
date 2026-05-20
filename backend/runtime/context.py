"""Runtime execution context - injectable dependencies for deterministic execution."""

import time
from typing import Callable, Dict, Any, Optional


class RuntimeExecutionContext:
    """Execution context with injectable time source and explicit state.

    Provides controllable time for replay and testing.
    All state is explicit and inspectable.
    """

    def __init__(self, time_source: Optional[Callable[[], float]] = None):
        """Initialize context with an optional injectable time source.

        Args:
            time_source: Callable returning current timestamp as float.
                         Defaults to time.time if not provided.
        """
        self._time_source: Callable[[], float] = time_source or time.time
        self._state: Dict[str, Any] = {}

    def now(self) -> float:
        """Get the current timestamp from the injectable time source."""
        return self._time_source()

    def now_iso(self) -> str:
        """Get the current timestamp as an ISO-format string."""
        import datetime

        ts = self.now()
        return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat()

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get explicit state by key."""
        return self._state.get(key, default)

    def set_state(self, key: str, value: Any) -> None:
        """Set explicit state by key."""
        self._state[key] = value

    def get_all_state(self) -> Dict[str, Any]:
        """Get all explicit state for inspection."""
        return dict(self._state)
