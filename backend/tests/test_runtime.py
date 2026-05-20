"""Tests for runtime module - lifecycle, registration, deterministic IDs."""

import pytest

from backend.runtime.context import RuntimeExecutionContext
from backend.runtime.manager import RuntimeManager
from backend.runtime.models import (
    Runtime,
    RuntimeRegistration,
    RuntimeState,
    generate_runtime_id,
)


def make_context(fixed_time: float = 1000000.0) -> RuntimeExecutionContext:
    """Create a context with a fixed time source for deterministic testing."""
    return RuntimeExecutionContext(time_source=lambda: fixed_time)


class TestDeterministicIds:
    """Test that runtime IDs are deterministic."""

    def test_same_inputs_produce_same_id(self):
        """Same name and timestamp always produce the same ID."""
        id1 = generate_runtime_id("test-runtime", "2024-01-01T00:00:00+00:00")
        id2 = generate_runtime_id("test-runtime", "2024-01-01T00:00:00+00:00")
        assert id1 == id2

    def test_different_names_produce_different_ids(self):
        """Different names produce different IDs."""
        id1 = generate_runtime_id("runtime-a", "2024-01-01T00:00:00+00:00")
        id2 = generate_runtime_id("runtime-b", "2024-01-01T00:00:00+00:00")
        assert id1 != id2

    def test_different_timestamps_produce_different_ids(self):
        """Different timestamps produce different IDs."""
        id1 = generate_runtime_id("test", "2024-01-01T00:00:00+00:00")
        id2 = generate_runtime_id("test", "2024-01-02T00:00:00+00:00")
        assert id1 != id2

    def test_id_is_hex_string(self):
        """IDs are 16-character hex strings."""
        rid = generate_runtime_id("test", "2024-01-01T00:00:00+00:00")
        assert len(rid) == 16
        assert all(c in "0123456789abcdef" for c in rid)


class TestRuntimeManager:
    """Test runtime manager lifecycle."""

    def test_register_runtime(self):
        """Registering a runtime creates it in INITIALIZING state."""
        ctx = make_context()
        manager = RuntimeManager(ctx)
        reg = RuntimeRegistration(name="test-runtime", metadata={"version": "1.0"})

        runtime = manager.register(reg)

        assert runtime.name == "test-runtime"
        assert runtime.state == RuntimeState.INITIALIZING
        assert runtime.metadata == {"version": "1.0"}
        assert runtime.id != ""
        assert manager.runtime_count == 1

    def test_get_runtime(self):
        """Can retrieve a runtime by its ID."""
        ctx = make_context()
        manager = RuntimeManager(ctx)
        reg = RuntimeRegistration(name="test")

        runtime = manager.register(reg)
        found = manager.get(runtime.id)

        assert found is not None
        assert found.id == runtime.id

    def test_get_nonexistent_runtime(self):
        """Getting a nonexistent runtime returns None."""
        ctx = make_context()
        manager = RuntimeManager(ctx)

        assert manager.get("nonexistent") is None

    def test_valid_transition_initializing_to_ready(self):
        """Can transition from INITIALIZING to READY."""
        ctx = make_context()
        manager = RuntimeManager(ctx)
        reg = RuntimeRegistration(name="test")
        runtime = manager.register(reg)

        updated = manager.transition(runtime.id, RuntimeState.READY)
        assert updated.state == RuntimeState.READY

    def test_valid_transition_ready_to_running(self):
        """Can transition from READY to RUNNING."""
        ctx = make_context()
        manager = RuntimeManager(ctx)
        reg = RuntimeRegistration(name="test")
        runtime = manager.register(reg)

        manager.transition(runtime.id, RuntimeState.READY)
        updated = manager.transition(runtime.id, RuntimeState.RUNNING)
        assert updated.state == RuntimeState.RUNNING

    def test_valid_transition_running_to_stopping(self):
        """Can transition from RUNNING to STOPPING."""
        ctx = make_context()
        manager = RuntimeManager(ctx)
        reg = RuntimeRegistration(name="test")
        runtime = manager.register(reg)

        manager.transition(runtime.id, RuntimeState.READY)
        manager.transition(runtime.id, RuntimeState.RUNNING)
        updated = manager.transition(runtime.id, RuntimeState.STOPPING)
        assert updated.state == RuntimeState.STOPPING

    def test_valid_transition_stopping_to_stopped(self):
        """Can transition from STOPPING to STOPPED."""
        ctx = make_context()
        manager = RuntimeManager(ctx)
        reg = RuntimeRegistration(name="test")
        runtime = manager.register(reg)

        manager.transition(runtime.id, RuntimeState.READY)
        manager.transition(runtime.id, RuntimeState.RUNNING)
        manager.transition(runtime.id, RuntimeState.STOPPING)
        updated = manager.transition(runtime.id, RuntimeState.STOPPED)
        assert updated.state == RuntimeState.STOPPED

    def test_invalid_transition_raises(self):
        """Invalid transitions raise ValueError."""
        ctx = make_context()
        manager = RuntimeManager(ctx)
        reg = RuntimeRegistration(name="test")
        runtime = manager.register(reg)

        with pytest.raises(ValueError, match="Invalid transition"):
            manager.transition(runtime.id, RuntimeState.STOPPED)

    def test_transition_nonexistent_raises(self):
        """Transitioning a nonexistent runtime raises ValueError."""
        ctx = make_context()
        manager = RuntimeManager(ctx)

        with pytest.raises(ValueError, match="Runtime not found"):
            manager.transition("nonexistent", RuntimeState.READY)

    def test_error_transition_from_any_active_state(self):
        """Can transition to ERROR from any active state."""
        ctx = make_context()
        manager = RuntimeManager(ctx)

        for initial_target in [RuntimeState.READY, RuntimeState.RUNNING]:
            reg = RuntimeRegistration(name=f"test-{initial_target}")
            runtime = manager.register(reg)
            if initial_target == RuntimeState.RUNNING:
                manager.transition(runtime.id, RuntimeState.READY)
            manager.transition(runtime.id, initial_target)
            updated = manager.transition(runtime.id, RuntimeState.ERROR)
            assert updated.state == RuntimeState.ERROR

    def test_list_runtimes(self):
        """Can list all registered runtimes."""
        ctx = make_context()
        manager = RuntimeManager(ctx)

        manager.register(RuntimeRegistration(name="rt-1"))
        manager.register(RuntimeRegistration(name="rt-2"))

        runtimes = manager.list_runtimes()
        assert len(runtimes) == 2


class TestRuntimeExecutionContext:
    """Test the execution context."""

    def test_injectable_time_source(self):
        """Time source is injectable and controllable."""
        ctx = RuntimeExecutionContext(time_source=lambda: 1234567890.0)
        assert ctx.now() == 1234567890.0

    def test_explicit_state(self):
        """State is explicit and inspectable."""
        ctx = RuntimeExecutionContext(time_source=lambda: 0.0)
        ctx.set_state("key", "value")
        assert ctx.get_state("key") == "value"
        assert ctx.get_all_state() == {"key": "value"}

    def test_default_state_returns_default(self):
        """Getting nonexistent state returns the provided default."""
        ctx = RuntimeExecutionContext(time_source=lambda: 0.0)
        assert ctx.get_state("missing", "default") == "default"
