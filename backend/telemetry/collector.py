"""Telemetry collector - runtime metrics, execution traces, event counters."""

import hashlib
from typing import Dict, List, Optional

from backend.runtime.context import RuntimeExecutionContext
from backend.telemetry.models import HealthState, MetricRecord, TraceRecord


class TelemetryCollector:
    """Collects and aggregates runtime metrics and traces.

    All telemetry is explicit and inspectable.
    """

    def __init__(self, context: RuntimeExecutionContext):
        """Initialize the telemetry collector.

        Args:
            context: Execution context providing time source.
        """
        self._context = context
        self._metrics: List[MetricRecord] = []
        self._traces: List[TraceRecord] = []
        self._counters: Dict[str, int] = {}

    def record_metric(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> MetricRecord:
        """Record a metric measurement.

        Args:
            name: Metric name.
            value: Metric value.
            labels: Optional labels for the metric.

        Returns:
            The created MetricRecord.
        """
        metric = MetricRecord(
            name=name,
            value=value,
            timestamp=self._context.now_iso(),
            labels=labels or {},
        )
        self._metrics.append(metric)
        return metric

    def start_trace(
        self, operation: str, metadata: Optional[Dict[str, str]] = None
    ) -> TraceRecord:
        """Start an execution trace.

        Args:
            operation: Name of the operation being traced.
            metadata: Optional trace metadata.

        Returns:
            The created TraceRecord (without end_timestamp).
        """
        timestamp = self._context.now_iso()
        trace_id = hashlib.sha256(
            f"{operation}{timestamp}".encode("utf-8")
        ).hexdigest()[:16]

        trace = TraceRecord(
            trace_id=trace_id,
            operation=operation,
            start_timestamp=timestamp,
            metadata=metadata or {},
        )
        self._traces.append(trace)
        return trace

    def increment_counter(self, name: str, amount: int = 1) -> int:
        """Increment an event counter.

        Args:
            name: Counter name.
            amount: Amount to increment by.

        Returns:
            The new counter value.
        """
        current = self._counters.get(name, 0)
        self._counters[name] = current + amount
        return self._counters[name]

    def get_metrics(self, limit: int = 100) -> List[MetricRecord]:
        """Get recent metrics.

        Args:
            limit: Maximum number of metrics to return.

        Returns:
            List of recent metrics.
        """
        return self._metrics[-limit:]

    def get_traces(self, limit: int = 100) -> List[TraceRecord]:
        """Get recent traces.

        Args:
            limit: Maximum number of traces to return.

        Returns:
            List of recent traces.
        """
        return self._traces[-limit:]

    def get_counters(self) -> Dict[str, int]:
        """Get all counters."""
        return dict(self._counters)

    @property
    def metric_count(self) -> int:
        """Total number of recorded metrics."""
        return len(self._metrics)

    @property
    def trace_count(self) -> int:
        """Total number of recorded traces."""
        return len(self._traces)
