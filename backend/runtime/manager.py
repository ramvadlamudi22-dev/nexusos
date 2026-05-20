"""Runtime manager - lifecycle management for governed runtimes."""

from typing import Dict, List, Optional

from backend.runtime.context import RuntimeExecutionContext
from backend.runtime.models import (
    Runtime,
    RuntimeRegistration,
    RuntimeState,
    generate_runtime_id,
)


# Valid state transitions
VALID_TRANSITIONS: Dict[RuntimeState, List[RuntimeState]] = {
    RuntimeState.INITIALIZING: [RuntimeState.READY, RuntimeState.ERROR],
    RuntimeState.READY: [RuntimeState.RUNNING, RuntimeState.STOPPING, RuntimeState.ERROR],
    RuntimeState.RUNNING: [RuntimeState.STOPPING, RuntimeState.ERROR],
    RuntimeState.STOPPING: [RuntimeState.STOPPED, RuntimeState.ERROR],
    RuntimeState.STOPPED: [],
    RuntimeState.ERROR: [RuntimeState.INITIALIZING],
}


class RuntimeManager:
    """Manages runtime lifecycle with explicit state transitions.

    All runtimes are stored in-memory with deterministic IDs.
    State transitions are validated against allowed transitions.
    """

    def __init__(self, context: RuntimeExecutionContext):
        """Initialize the runtime manager.

        Args:
            context: Execution context providing time source and state.
        """
        self._context = context
        self._runtimes: Dict[str, Runtime] = {}

    def register(self, registration: RuntimeRegistration) -> Runtime:
        """Register a new runtime with deterministic ID generation.

        Args:
            registration: Runtime registration data.

        Returns:
            The newly created Runtime instance.
        """
        timestamp = self._context.now_iso()
        runtime_id = generate_runtime_id(registration.name, timestamp)

        runtime = Runtime(
            id=runtime_id,
            name=registration.name,
            state=RuntimeState.INITIALIZING,
            metadata=registration.metadata,
            creation_timestamp=timestamp,
        )

        self._runtimes[runtime_id] = runtime
        return runtime

    def get(self, runtime_id: str) -> Optional[Runtime]:
        """Get a runtime by ID.

        Args:
            runtime_id: The deterministic runtime ID.

        Returns:
            The Runtime instance, or None if not found.
        """
        return self._runtimes.get(runtime_id)

    def transition(self, runtime_id: str, new_state: RuntimeState) -> Runtime:
        """Transition a runtime to a new state.

        Args:
            runtime_id: The runtime to transition.
            new_state: The target state.

        Returns:
            The updated Runtime instance.

        Raises:
            ValueError: If the runtime is not found or transition is invalid.
        """
        runtime = self._runtimes.get(runtime_id)
        if runtime is None:
            raise ValueError(f"Runtime not found: {runtime_id}")

        allowed = VALID_TRANSITIONS.get(runtime.state, [])
        if new_state not in allowed:
            raise ValueError(
                f"Invalid transition from {runtime.state} to {new_state}"
            )

        runtime.state = new_state
        return runtime

    def list_runtimes(self) -> List[Runtime]:
        """List all registered runtimes."""
        return list(self._runtimes.values())

    @property
    def runtime_count(self) -> int:
        """Get the number of registered runtimes."""
        return len(self._runtimes)
