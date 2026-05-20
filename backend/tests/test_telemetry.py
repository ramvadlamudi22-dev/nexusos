"""Tests for telemetry module - metrics collection, health state."""

from backend.runtime.context import RuntimeExecutionContext
from backend.telemetry.collector import TelemetryCollector
from backend.telemetry.health import RuntimeHealthMonitor
from backend.telemetry.models import HealthState


def make_context(fixed_time: float = 1000000.0) -> RuntimeExecutionContext:
    """Create a context with a fixed time source for deterministic testing."""
    return RuntimeExecutionContext(time_source=lambda: fixed_time)


class TestTelemetryCollector:
    """Test metrics and trace collection."""

    def test_record_metric(self):
        """Can record a metric with value and labels."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)

        metric = collector.record_metric(
            name="cpu_usage", value=45.5, labels={"host": "node-1"}
        )

        assert metric.name == "cpu_usage"
        assert metric.value == 45.5
        assert metric.labels == {"host": "node-1"}
        assert metric.timestamp != ""

    def test_get_metrics(self):
        """Can retrieve recorded metrics."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)

        collector.record_metric("m1", 1.0)
        collector.record_metric("m2", 2.0)

        metrics = collector.get_metrics()
        assert len(metrics) == 2
        assert metrics[0].name == "m1"
        assert metrics[1].name == "m2"

    def test_start_trace(self):
        """Can start an execution trace."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)

        trace = collector.start_trace("runtime.register", {"runtime": "test"})

        assert trace.operation == "runtime.register"
        assert trace.trace_id != ""
        assert trace.start_timestamp != ""
        assert collector.trace_count == 1

    def test_increment_counter(self):
        """Can increment event counters."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)

        assert collector.increment_counter("events") == 1
        assert collector.increment_counter("events") == 2
        assert collector.increment_counter("errors") == 1

        counters = collector.get_counters()
        assert counters == {"events": 2, "errors": 1}

    def test_metric_count(self):
        """metric_count tracks total recorded metrics."""
        ctx = make_context()
        collector = TelemetryCollector(ctx)

        assert collector.metric_count == 0
        collector.record_metric("test", 1.0)
        assert collector.metric_count == 1


class TestRuntimeHealthMonitor:
    """Test health state tracking."""

    def test_initial_state_unknown(self):
        """Initial overall state is UNKNOWN."""
        ctx = make_context()
        monitor = RuntimeHealthMonitor(ctx)

        assert monitor.get_overall_health() == HealthState.UNKNOWN

    def test_all_healthy(self):
        """Overall is HEALTHY when all components are HEALTHY."""
        ctx = make_context()
        monitor = RuntimeHealthMonitor(ctx)

        monitor.update_component("runtime", HealthState.HEALTHY)
        monitor.update_component("events", HealthState.HEALTHY)

        assert monitor.get_overall_health() == HealthState.HEALTHY

    def test_any_unhealthy_makes_overall_unhealthy(self):
        """Overall is UNHEALTHY when any component is UNHEALTHY."""
        ctx = make_context()
        monitor = RuntimeHealthMonitor(ctx)

        monitor.update_component("runtime", HealthState.HEALTHY)
        monitor.update_component("events", HealthState.UNHEALTHY)

        assert monitor.get_overall_health() == HealthState.UNHEALTHY

    def test_degraded_state(self):
        """Overall is DEGRADED when component is DEGRADED but none UNHEALTHY."""
        ctx = make_context()
        monitor = RuntimeHealthMonitor(ctx)

        monitor.update_component("runtime", HealthState.HEALTHY)
        monitor.update_component("events", HealthState.DEGRADED)

        assert monitor.get_overall_health() == HealthState.DEGRADED

    def test_get_component_health(self):
        """Can get individual component health."""
        ctx = make_context()
        monitor = RuntimeHealthMonitor(ctx)

        monitor.update_component("runtime", HealthState.HEALTHY)

        assert monitor.get_component_health("runtime") == HealthState.HEALTHY
        assert monitor.get_component_health("unknown") == HealthState.UNKNOWN

    def test_get_all_components(self):
        """Can get all component health states."""
        ctx = make_context()
        monitor = RuntimeHealthMonitor(ctx)

        monitor.update_component("a", HealthState.HEALTHY)
        monitor.update_component("b", HealthState.DEGRADED)

        components = monitor.get_all_components()
        assert components == {"a": HealthState.HEALTHY, "b": HealthState.DEGRADED}
