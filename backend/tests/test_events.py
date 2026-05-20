"""Tests for events module - dispatch, subscribe, replay-safe structure."""

from backend.events.bus import EventBus
from backend.events.models import BaseEvent, EventType
from backend.runtime.context import RuntimeExecutionContext


def make_context(fixed_time: float = 1000000.0) -> RuntimeExecutionContext:
    """Create a context with a fixed time source for deterministic testing."""
    return RuntimeExecutionContext(time_source=lambda: fixed_time)


class TestEventBus:
    """Test the event bus dispatch and subscription."""

    def test_dispatch_creates_event(self):
        """Dispatching creates a typed event with sequence number."""
        ctx = make_context()
        bus = EventBus(ctx)

        event = bus.dispatch(EventType.RUNTIME, {"action": "register"})

        assert event.event_type == EventType.RUNTIME
        assert event.sequence == 1
        assert event.payload == {"action": "register"}
        assert event.id != ""
        assert event.timestamp != ""

    def test_dispatch_increments_sequence(self):
        """Each dispatch increments the sequence number."""
        ctx = make_context()
        bus = EventBus(ctx)

        e1 = bus.dispatch(EventType.RUNTIME, {})
        e2 = bus.dispatch(EventType.GOVERNANCE, {})
        e3 = bus.dispatch(EventType.TELEMETRY, {})

        assert e1.sequence == 1
        assert e2.sequence == 2
        assert e3.sequence == 3

    def test_subscribe_receives_events(self):
        """Subscribers receive dispatched events."""
        ctx = make_context()
        bus = EventBus(ctx)
        received = []

        bus.subscribe(EventType.RUNTIME, lambda e: received.append(e))
        bus.dispatch(EventType.RUNTIME, {"action": "test"})

        assert len(received) == 1
        assert received[0].payload == {"action": "test"}

    def test_subscriber_only_gets_subscribed_type(self):
        """Subscribers only receive events of their subscribed type."""
        ctx = make_context()
        bus = EventBus(ctx)
        runtime_events = []
        governance_events = []

        bus.subscribe(EventType.RUNTIME, lambda e: runtime_events.append(e))
        bus.subscribe(EventType.GOVERNANCE, lambda e: governance_events.append(e))

        bus.dispatch(EventType.RUNTIME, {"action": "register"})
        bus.dispatch(EventType.GOVERNANCE, {"action": "validate"})

        assert len(runtime_events) == 1
        assert len(governance_events) == 1
        assert runtime_events[0].event_type == EventType.RUNTIME
        assert governance_events[0].event_type == EventType.GOVERNANCE

    def test_multiple_subscribers(self):
        """Multiple subscribers receive the same event."""
        ctx = make_context()
        bus = EventBus(ctx)
        received_a = []
        received_b = []

        bus.subscribe(EventType.RUNTIME, lambda e: received_a.append(e))
        bus.subscribe(EventType.RUNTIME, lambda e: received_b.append(e))
        bus.dispatch(EventType.RUNTIME, {"action": "test"})

        assert len(received_a) == 1
        assert len(received_b) == 1

    def test_get_events_returns_log(self):
        """get_events returns the event log."""
        ctx = make_context()
        bus = EventBus(ctx)

        bus.dispatch(EventType.RUNTIME, {"n": 1})
        bus.dispatch(EventType.RUNTIME, {"n": 2})

        events = bus.get_events()
        assert len(events) == 2
        assert events[0].payload == {"n": 1}
        assert events[1].payload == {"n": 2}

    def test_get_event_by_id(self):
        """Can retrieve a specific event by ID."""
        ctx = make_context()
        bus = EventBus(ctx)

        event = bus.dispatch(EventType.RUNTIME, {"action": "find-me"})
        found = bus.get_event(event.id)

        assert found is not None
        assert found.id == event.id
        assert found.payload == {"action": "find-me"}

    def test_get_event_not_found(self):
        """Getting a nonexistent event returns None."""
        ctx = make_context()
        bus = EventBus(ctx)

        assert bus.get_event("nonexistent") is None

    def test_deterministic_event_ids(self):
        """Events with same type, sequence, and timestamp get same ID."""
        ctx = make_context(fixed_time=1000000.0)
        bus1 = EventBus(ctx)
        bus2 = EventBus(ctx)

        e1 = bus1.dispatch(EventType.RUNTIME, {"action": "test"})
        e2 = bus2.dispatch(EventType.RUNTIME, {"action": "test"})

        # Same time source, same sequence, same type -> same ID
        assert e1.id == e2.id

    def test_event_count(self):
        """event_count tracks total dispatched events."""
        ctx = make_context()
        bus = EventBus(ctx)

        assert bus.event_count == 0
        bus.dispatch(EventType.RUNTIME, {})
        assert bus.event_count == 1
        bus.dispatch(EventType.GOVERNANCE, {})
        assert bus.event_count == 2
