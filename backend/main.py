"""
NexusOS Backend - Production Runtime Entry Point
"""

import os
import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import create_router
from backend.api.execution_routes import create_execution_router
from backend.api.verify_routes import create_verify_router

from backend.auth.api_keys import AuthManager

from backend.logging_config import configure_logging

from backend.browser.runtime import BrowserRuntime
from backend.events.bus import EventBus

from backend.governance.audit import AuditLogger
from backend.governance.engine import GovernanceEngine
from backend.governance.execution import ExecutionGovernanceValidator
from backend.governance.models import (
    Permission,
    PermissionLevel,
    Policy,
)

from backend.replay.execution import ExecutionReplayManager
from backend.replay.recorder import ReplayRecorder

from backend.runtime.context import RuntimeExecutionContext
from backend.runtime.manager import RuntimeManager

from backend.skills.runtime import SkillRuntime

from backend.telemetry.collector import TelemetryCollector
from backend.telemetry.execution import ExecutionTelemetryCollector
from backend.telemetry.health import RuntimeHealthMonitor
from backend.telemetry.models import HealthState

from backend.terminal.runtime import TerminalRuntime

from backend.verify.engine import VerificationEngine

from backend.workflow.engine import WorkflowEngine


def create_app() -> FastAPI:
    """
    Create NexusOS FastAPI application.
    """

    structured_logs = (
        os.environ.get("NEXUSOS_LOG_FORMAT", "json") == "json"
    )

    configure_logging(structured=structured_logs)

    context = RuntimeExecutionContext()

    # Core systems
    runtime_manager = RuntimeManager(context)
    event_bus = EventBus(context)

    governance_engine = GovernanceEngine(context)
    audit_logger = AuditLogger(context)

    telemetry_collector = TelemetryCollector(context)
    health_monitor = RuntimeHealthMonitor(context)

    replay_recorder = ReplayRecorder(context)

    # Runtime systems
    browser_runtime = BrowserRuntime(context)
    terminal_runtime = TerminalRuntime(context)
    workflow_engine = WorkflowEngine(context)
    skill_runtime = SkillRuntime(context)

    # Execution integrations
    governance_validator = ExecutionGovernanceValidator(
        context,
        governance_engine,
    )

    execution_telemetry = ExecutionTelemetryCollector(
        context,
        telemetry_collector,
    )

    replay_manager = ExecutionReplayManager(
        context,
        replay_recorder,
    )

    # Default governance policy
    default_policy = Policy(
        id="default-allow-all",
        name="Default Allow All",
        description="Development fallback policy",
        permissions=[
            Permission(
                action="*",
                level=PermissionLevel.ALLOW,
                resource="*",
            )
        ],
        active=True,
    )

    governance_engine.register_policy(default_policy)

    # FastAPI app
    app = FastAPI(
        title="NexusOS Runtime Platform",
        description="Governed operational verification platform",
        version="0.2.0",
    )

    # CORS
    cors_origins_raw = os.environ.get(
        "NEXUSOS_CORS_ORIGINS",
        "*"
    )

    if cors_origins_raw == "*":
        cors_origins = ["*"]
    else:
        cors_origins = [
            origin.strip()
            for origin in cors_origins_raw.split(",")
            if origin.strip()
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=cors_origins != ["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Core API router
    app.include_router(
        create_router(
            context=context,
            runtime_manager=runtime_manager,
            event_bus=event_bus,
            governance_engine=governance_engine,
            audit_logger=audit_logger,
            telemetry_collector=telemetry_collector,
            health_monitor=health_monitor,
            replay_recorder=replay_recorder,
        )
    )

    # Execution router
    app.include_router(
        create_execution_router(
            context=context,
            browser_runtime=browser_runtime,
            terminal_runtime=terminal_runtime,
            workflow_engine=workflow_engine,
            skill_runtime=skill_runtime,
            governance_validator=governance_validator,
            telemetry_collector=execution_telemetry,
            replay_manager=replay_manager,
        )
    )

    # Verification router
    verification_engine = VerificationEngine(
        context=context,
        governance_engine=governance_engine,
        audit_logger=audit_logger,
        telemetry_collector=telemetry_collector,
    )

    auth_manager = AuthManager()

    app.include_router(
        create_verify_router(
            verification_engine,
            auth_manager,
        )
    )

    # Health state registration
    healthy_components = [
        "runtime_manager",
        "event_bus",
        "governance_engine",
        "telemetry_collector",
        "replay_recorder",
        "browser_runtime",
        "terminal_runtime",
        "workflow_engine",
        "skill_runtime",
        "verification_engine",
    ]

    for component in healthy_components:
        health_monitor.update_component(
            component,
            HealthState.HEALTHY,
        )

    # Production health endpoint
    @app.get("/api/health")
    def health():
        return {
            "status": "healthy",
            "service": "NexusOS",
            "version": "0.2.0",
        }

    # OpenAPI endpoint
    @app.get("/api/openapi")
    def get_openapi_schema():
        return app.openapi()

    # Endpoint discovery
    @app.get("/api/docs/endpoints")
    def get_endpoints_list():
        endpoints = []

        for route in app.routes:
            if hasattr(route, "methods") and hasattr(route, "path"):
                endpoints.append(
                    {
                        "path": route.path,
                        "methods": sorted(route.methods),
                        "name": route.name,
                    }
                )

        return {
            "endpoints": endpoints
        }

    return app


# Application instance
app = create_app()


# Railway / Production runtime entrypoint
if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
    )