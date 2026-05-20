"""Event bus - internal dispatcher with typed subscriptions and event logging."""

import hashlib
from typing import Any, Callable, Dict, List, Optional, Type

from backend.events.models import BaseEvent, EventType
from backend.runtime.context import RuntimeExecutionContext


class EventBus:
    """Internal event dispatcher with typed subscriptions.

    Maintains a sequence counter for replay-safe event ordering.
    All events are logged for observability.
    """

    def __init__(self, context: RuntimeExecutionContext):
        """Initialize the event bus.

        Args:
            context: Execution context providing time source.
        """
        self._context = context
        self._subscribers: Dict[EventType, List[Callable[[BaseEvent], None]]] = {}
        self._event_log: List[BaseEvent] = []
        self._sequence: int = 0

    def subscribe(
        self, event_type: EventType, callback: Callable[[BaseEvent], None]
    ) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: The type of events to subscribe to.
            callback: Function to call when an event of this type is dispatched.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def dispatch(self, event_type: EventType, payload: Dict[str, Any]) -> BaseEvent:
        """Dispatch a typed event to all subscribers.

        Creates a replay-safe event with sequence number and deterministic ID.

        Args:
            event_type: The type of event to dispatch.
            payload: Event payload data.

        Returns:
            The created BaseEvent instance.
        """
        self._sequence += 1
        timestamp = self._context.now_iso()

        event_id = hashlib.sha256(
            f"{event_type.value}{self._sequence}{payload}".encode("utf-8")
        ).hexdigest()[:16]

        event = BaseEvent(
            id=event_id,
            event_type=event_type,
            timestamp=timestamp,
            sequence=self._sequence,
            payload=payload,
        )

        self._event_log.append(event)

        subscribers = self._subscribers.get(event_type, [])
        for callback in subscribers:
            callback(event)

        return event

    def get_events(self, limit: int = 100) -> List[BaseEvent]:
        """Get recent events from the log.

        Args:
            limit: Maximum number of events to return.

        Returns:
            List of recent events, most recent last.
        """
        return self._event_log[-limit:]

    def get_event(self, event_id: str) -> Optional[BaseEvent]:
        """Get a specific event by ID.

        Args:
            event_id: The event ID to look up.

        Returns:
            The event if found, None otherwise.
        """
        for event in self._event_log:
            if event.id == event_id:
                return event
        return None

    @property
    def event_count(self) -> int:
        """Get the total number of events dispatched."""
        return len(self._event_log)

    @property
    def current_sequence(self) -> int:
        """Get the current sequence number."""
        return self._sequence
