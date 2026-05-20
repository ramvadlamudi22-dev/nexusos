"""Runtime health monitor - tracks system health state."""

from typing import Dict, List

from backend.runtime.context import RuntimeExecutionContext
from backend.telemetry.models import HealthState


class RuntimeHealthMonitor:
    """Monitors and tracks runtime health state.

    Health state is explicit and inspectable.
    Tracks individual component health and computes overall state.
    """

    def __init__(self, context: RuntimeExecutionContext):
        """Initialize the health monitor.

        Args:
            context: Execution context providing time source.
        """
        self._context = context
        self._component_health: Dict[str, HealthState] = {}
        self._overall_state: HealthState = HealthState.UNKNOWN

    def update_component(self, component: str, state: HealthState) -> None:
        """Update the health state of a component.

        Args:
            component: Component name.
            state: New health state.
        """
        self._component_health[component] = state
        self._recompute_overall()

    def get_component_health(self, component: str) -> HealthState:
        """Get the health state of a specific component.

        Args:
            component: Component name.

        Returns:
            The component's health state, or UNKNOWN if not tracked.
        """
        return self._component_health.get(component, HealthState.UNKNOWN)

    def get_overall_health(self) -> HealthState:
        """Get the overall system health state."""
        return self._overall_state

    def get_all_components(self) -> Dict[str, HealthState]:
        """Get health state of all tracked components."""
        return dict(self._component_health)

    def _recompute_overall(self) -> None:
        """Recompute overall health from component states."""
        if not self._component_health:
            self._overall_state = HealthState.UNKNOWN
            return

        states = list(self._component_health.values())

        if all(s == HealthState.HEALTHY for s in states):
            self._overall_state = HealthState.HEALTHY
        elif any(s == HealthState.UNHEALTHY for s in states):
            self._overall_state = HealthState.UNHEALTHY
        elif any(s == HealthState.DEGRADED for s in states):
            self._overall_state = HealthState.DEGRADED
        else:
            self._overall_state = HealthState.UNKNOWN
