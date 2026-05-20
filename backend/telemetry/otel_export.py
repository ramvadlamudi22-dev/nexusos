"""OpenTelemetry export — sends traces and metrics to OTEL-compatible backends.

Supports: Datadog, Grafana, New Relic, Jaeger, or any OTLP endpoint.
Falls back to no-op when OTEL endpoint is not configured.
"""

import os
import json
import time
from typing import Any, Dict, List, Optional


class OTELExporter:
    """Exports NexusOS telemetry in OpenTelemetry format.

    When OTEL_EXPORTER_OTLP_ENDPOINT is set, sends traces and metrics
    to the configured OTLP endpoint. Otherwise, operates as no-op.
    """

    def __init__(self):
        self._endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        self._service_name = os.environ.get("OTEL_SERVICE_NAME", "nexusos")
        self._headers = {}

        # Parse auth headers if provided
        headers_raw = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS", "")
        if headers_raw:
            for pair in headers_raw.split(","):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    self._headers[k.strip()] = v.strip()

        self._enabled = bool(self._endpoint)
        self._buffer: List[Dict[str, Any]] = []

    @property
    def enabled(self) -> bool:
        """Whether OTEL export is configured."""
        return self._enabled

    def export_verification_span(
        self,
        execution_id: str,
        target_url: str,
        verdict: str,
        score: int,
        duration_ms: float,
        pages_checked: int,
        apis_checked: int,
    ) -> None:
        """Export a verification execution as an OTEL span.

        Args:
            execution_id: Unique execution ID.
            target_url: Verified target.
            verdict: PASS/FAIL/DEGRADED.
            score: Verification score.
            duration_ms: Execution duration.
            pages_checked: Number of pages verified.
            apis_checked: Number of APIs checked.
        """
        span = {
            "traceId": execution_id.ljust(32, "0"),
            "spanId": execution_id[:16],
            "name": "nexusos.verify",
            "kind": "SPAN_KIND_INTERNAL",
            "startTimeUnixNano": int((time.time() - duration_ms / 1000) * 1e9),
            "endTimeUnixNano": int(time.time() * 1e9),
            "attributes": [
                {"key": "nexusos.target_url", "value": {"stringValue": target_url}},
                {"key": "nexusos.verdict", "value": {"stringValue": verdict}},
                {"key": "nexusos.score", "value": {"intValue": score}},
                {"key": "nexusos.pages_checked", "value": {"intValue": pages_checked}},
                {"key": "nexusos.apis_checked", "value": {"intValue": apis_checked}},
                {"key": "service.name", "value": {"stringValue": self._service_name}},
            ],
            "status": {
                "code": "STATUS_CODE_OK" if verdict == "PASS" else "STATUS_CODE_ERROR",
            },
        }

        self._buffer.append(span)

        if self._enabled:
            self._flush()

    def export_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Export a metric data point."""
        if not self._enabled:
            return

        # Buffer metric for batch export
        metric = {
            "name": f"nexusos.{name}",
            "value": value,
            "timestamp": int(time.time() * 1e9),
            "labels": labels or {},
        }
        self._buffer.append(metric)

    def _flush(self) -> None:
        """Flush buffered telemetry to OTLP endpoint."""
        if not self._endpoint or not self._buffer:
            return

        try:
            import httpx

            payload = {
                "resourceSpans": [
                    {
                        "resource": {
                            "attributes": [
                                {"key": "service.name", "value": {"stringValue": self._service_name}},
                                {"key": "service.version", "value": {"stringValue": "0.2.0"}},
                            ]
                        },
                        "scopeSpans": [
                            {
                                "scope": {"name": "nexusos.verify"},
                                "spans": [s for s in self._buffer if "traceId" in s],
                            }
                        ],
                    }
                ]
            }

            # Synchronous export (fire-and-forget for now)
            with httpx.Client(timeout=5.0) as client:
                client.post(
                    f"{self._endpoint}/v1/traces",
                    json=payload,
                    headers={**self._headers, "Content-Type": "application/json"},
                )

            self._buffer.clear()
        except Exception:
            # Don't let export failures break verification
            pass

    def get_config(self) -> Dict[str, Any]:
        """Get current OTEL configuration (for dashboard display)."""
        return {
            "enabled": self._enabled,
            "endpoint": self._endpoint or "not configured",
            "service_name": self._service_name,
            "buffer_size": len(self._buffer),
        }
