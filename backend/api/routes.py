"""FastAPI router with all NexusOS API endpoints."""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from backend.events.bus import EventBus
from backend.events.models import EventType
from backend.governance.audit import AuditLogger
from backend.governance.engine import GovernanceEngine
from backend.replay.recorder import ReplayRecorder
from backend.runtime.context import RuntimeExecutionContext
from backend.runtime.manager import RuntimeManager
from backend.runtime.models import RuntimeRegistration
from backend.telemetry.collector import TelemetryCollector
from backend.telemetry.health import RuntimeHealthMonitor


def create_router(
    context: RuntimeExecutionContext,
    runtime_manager: RuntimeManager,
    event_bus: EventBus,
    governance_engine: GovernanceEngine,
    audit_logger: AuditLogger,
    telemetry_collector: TelemetryCollector,
    health_monitor: RuntimeHealthMonitor,
    replay_recorder: ReplayRecorder,
) -> APIRouter:
    """Create the API router with injected dependencies.

    Args:
        context: Execution context.
        runtime_manager: Runtime lifecycle manager.
        event_bus: Event dispatcher.
        governance_engine: Policy enforcement engine.
        audit_logger: Audit record logger.
        telemetry_collector: Metrics collector.
        health_monitor: Health state monitor.
        replay_recorder: Operation recorder.

    Returns:
        Configured APIRouter.
    """
    router = APIRouter(prefix="/api")

    @router.get("/status")
    def get_status() -> Dict[str, Any]:
        """Get overall system status."""
        return {
            "status": "operational",
            "timestamp": context.now_iso(),
            "components": {
                "runtime_manager": {
                    "runtime_count": runtime_manager.runtime_count,
                },
                "event_bus": {
                    "event_count": event_bus.event_count,
                    "current_sequence": event_bus.current_sequence,
                },
                "governance_engine": {
                    "policy_count": governance_engine.policy_count,
                    "active": governance_engine.active,
                },
                "telemetry_collector": {
                    "metric_count": telemetry_collector.metric_count,
                    "trace_count": telemetry_collector.trace_count,
                },
                "replay_recorder": {
                    "record_count": replay_recorder.record_count,
                    "current_sequence": replay_recorder.current_sequence,
                },
            },
        }

    @router.post("/runtime/register")
    def register_runtime(registration: RuntimeRegistration) -> Dict[str, Any]:
        """Register a new runtime."""
        # Validate action through governance engine before executing
        result = governance_engine.validate_action("runtime.register")
        if not result.permitted:
            audit_logger.log(
                action="runtime.register",
                actor="api",
                outcome="denied",
                metadata={"reason": result.reason},
            )
            raise HTTPException(status_code=403, detail=result.reason)

        # Governance approved - log the approval
        audit_logger.log(
            action="runtime.register",
            actor="api",
            outcome="permitted",
            metadata={"policy_id": result.policy_id},
        )

        # Dispatch event
        event_bus.dispatch(
            EventType.RUNTIME,
            {"action": "register", "name": registration.name},
        )

        # Register the runtime
        runtime = runtime_manager.register(registration)

        # Record the operation for replay (after execution, with outputs)
        replay_recorder.record(
            operation="runtime.register",
            inputs={"name": registration.name, "metadata": registration.metadata},
            outputs={"id": runtime.id, "state": runtime.state.value},
        )

        # Record metric
        telemetry_collector.increment_counter("runtime.registrations")

        return {
            "id": runtime.id,
            "name": runtime.name,
            "state": runtime.state.value,
            "creation_timestamp": runtime.creation_timestamp,
            "metadata": runtime.metadata,
        }

    @router.get("/runtime/{runtime_id}/status")
    def get_runtime_status(runtime_id: str) -> Dict[str, Any]:
        """Get the status of a specific runtime."""
        runtime = runtime_manager.get(runtime_id)
        if runtime is None:
            raise HTTPException(status_code=404, detail="Runtime not found")
        return {
            "id": runtime.id,
            "name": runtime.name,
            "state": runtime.state.value,
            "creation_timestamp": runtime.creation_timestamp,
            "metadata": runtime.metadata,
        }

    @router.get("/events")
    def list_events() -> Dict[str, Any]:
        """List recent events."""
        events = event_bus.get_events()
        return {
            "events": [event.model_dump() for event in events],
            "total": event_bus.event_count,
        }

    @router.get("/events/{event_id}")
    def get_event(event_id: str) -> Dict[str, Any]:
        """Get a specific event by ID."""
        event = event_bus.get_event(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        return event.model_dump()

    @router.get("/governance/status")
    def get_governance_status() -> Dict[str, Any]:
        """Get governance engine status."""
        return {
            "active": governance_engine.active,
            "policy_count": governance_engine.policy_count,
            "policies": [
                {"id": p.id, "name": p.name, "active": p.active}
                for p in governance_engine.list_policies()
            ],
        }

    @router.get("/telemetry/status")
    def get_telemetry_status() -> Dict[str, Any]:
        """Get telemetry collector status."""
        return {
            "metric_count": telemetry_collector.metric_count,
            "trace_count": telemetry_collector.trace_count,
            "counters": telemetry_collector.get_counters(),
        }

    @router.get("/telemetry/metrics")
    def list_metrics() -> Dict[str, Any]:
        """List collected metrics."""
        metrics = telemetry_collector.get_metrics()
        return {
            "metrics": [m.model_dump() for m in metrics],
            "total": telemetry_collector.metric_count,
        }

    @router.get("/telemetry/health")
    def get_health() -> Dict[str, Any]:
        """Get system health state."""
        return {
            "overall": health_monitor.get_overall_health().value,
            "components": {
                name: state.value
                for name, state in health_monitor.get_all_components().items()
            },
        }

    @router.get("/health")
    def get_operational_health() -> Dict[str, Any]:
        """Get operational health for all subsystems.

        This is a deployment-level health endpoint distinct from /api/telemetry/health.
        Returns structured health for all subsystems with an overall status.
        """
        components = health_monitor.get_all_components()
        subsystems = [
            "runtime_manager",
            "event_bus",
            "governance_engine",
            "telemetry_collector",
            "replay_recorder",
            "browser_runtime",
            "terminal_runtime",
            "workflow_engine",
            "skill_runtime",
        ]
        subsystem_health = {}
        for subsystem in subsystems:
            if subsystem in components:
                subsystem_health[subsystem] = {"status": components[subsystem].value}
            else:
                subsystem_health[subsystem] = {"status": "UNKNOWN"}
        return {
            "overall": health_monitor.get_overall_health().value,
            "timestamp": context.now_iso(),
            "subsystems": subsystem_health,
        }

    @router.get("/governance/audit")
    def get_governance_audit() -> Dict[str, Any]:
        """Get governance audit records."""
        records = audit_logger.get_records()
        return {
            "records": [record.model_dump() for record in records],
            "total": len(records),
        }

    return router
