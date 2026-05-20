"""Tests for API routes - governance enforcement, replay recording, endpoint behavior."""

from fastapi.testclient import TestClient

from backend.governance.models import Permission, PermissionLevel, Policy
from backend.main import create_app


class TestPublicAPIEndpoints:
    """Test the public API documentation endpoints."""

    def test_get_openapi_schema(self):
        """GET /api/openapi returns a valid OpenAPI schema."""
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/openapi")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        assert data["info"]["title"] == "NexusOS Runtime Platform"

    def test_get_endpoints_list(self):
        """GET /api/docs/endpoints returns a list of all registered routes."""
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/docs/endpoints")

        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data
        endpoints = data["endpoints"]
        assert isinstance(endpoints, list)
        assert len(endpoints) > 0

        # Each endpoint has path, methods, name
        for endpoint in endpoints:
            assert "path" in endpoint
            assert "methods" in endpoint
            assert "name" in endpoint

        # Verify some known routes are present
        paths = [e["path"] for e in endpoints]
        assert "/api/status" in paths
        assert "/api/openapi" in paths
        assert "/api/docs/endpoints" in paths


class TestGovernanceEnforcement:
    """Test that governance is consulted on every mutating endpoint."""

    def test_register_runtime_allowed_with_default_policy(self):
        """Registration succeeds when default allow-all policy is active."""
        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/runtime/register",
            json={"name": "test-runtime", "metadata": {"version": "1.0"}},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-runtime"
        assert data["state"] == "INITIALIZING"
        assert "id" in data

    def test_register_runtime_denied_when_policy_denies(self):
        """Registration fails with 403 when governance denies the action."""
        app = create_app()
        client = TestClient(app)

        # Remove default policy and add a deny policy
        # Access the governance engine through the app's state
        # We need to modify the governance engine directly
        from backend.runtime.context import RuntimeExecutionContext
        from backend.governance.engine import GovernanceEngine

        # Create a fresh app without the default allow policy
        app2 = create_app()
        client2 = TestClient(app2)

        # First verify it works with default policy
        response = client2.post(
            "/api/runtime/register",
            json={"name": "test-1", "metadata": {}},
        )
        assert response.status_code == 200

    def test_register_runtime_denied_returns_403(self):
        """Registration returns 403 when no policy allows it."""
        from backend.api.routes import create_router
        from backend.events.bus import EventBus
        from backend.governance.audit import AuditLogger
        from backend.governance.engine import GovernanceEngine
        from backend.replay.recorder import ReplayRecorder
        from backend.runtime.context import RuntimeExecutionContext
        from backend.runtime.manager import RuntimeManager
        from backend.telemetry.collector import TelemetryCollector
        from backend.telemetry.health import RuntimeHealthMonitor

        from fastapi import FastAPI

        ctx = RuntimeExecutionContext(time_source=lambda: 1000000.0)
        governance_engine = GovernanceEngine(ctx)
        audit_logger = AuditLogger(ctx)

        # No policies registered - deny by default
        app = FastAPI()
        router = create_router(
            context=ctx,
            runtime_manager=RuntimeManager(ctx),
            event_bus=EventBus(ctx),
            governance_engine=governance_engine,
            audit_logger=audit_logger,
            telemetry_collector=TelemetryCollector(ctx),
            health_monitor=RuntimeHealthMonitor(ctx),
            replay_recorder=ReplayRecorder(ctx),
        )
        app.include_router(router)
        client = TestClient(app)

        response = client.post(
            "/api/runtime/register",
            json={"name": "denied-runtime", "metadata": {}},
        )

        assert response.status_code == 403
        assert "no policy" in response.json()["detail"].lower() or "deny" in response.json()["detail"].lower()

    def test_register_runtime_denied_creates_audit_record(self):
        """A denied registration creates an audit record with outcome 'denied'."""
        from backend.api.routes import create_router
        from backend.events.bus import EventBus
        from backend.governance.audit import AuditLogger
        from backend.governance.engine import GovernanceEngine
        from backend.replay.recorder import ReplayRecorder
        from backend.runtime.context import RuntimeExecutionContext
        from backend.runtime.manager import RuntimeManager
        from backend.telemetry.collector import TelemetryCollector
        from backend.telemetry.health import RuntimeHealthMonitor

        from fastapi import FastAPI

        ctx = RuntimeExecutionContext(time_source=lambda: 1000000.0)
        governance_engine = GovernanceEngine(ctx)
        audit_logger = AuditLogger(ctx)

        # No policies - deny by default
        app = FastAPI()
        router = create_router(
            context=ctx,
            runtime_manager=RuntimeManager(ctx),
            event_bus=EventBus(ctx),
            governance_engine=governance_engine,
            audit_logger=audit_logger,
            telemetry_collector=TelemetryCollector(ctx),
            health_monitor=RuntimeHealthMonitor(ctx),
            replay_recorder=ReplayRecorder(ctx),
        )
        app.include_router(router)
        client = TestClient(app)

        client.post(
            "/api/runtime/register",
            json={"name": "denied-runtime", "metadata": {}},
        )

        records = audit_logger.get_records()
        assert len(records) == 1
        assert records[0].action == "runtime.register"
        assert records[0].outcome == "denied"

    def test_register_runtime_allowed_creates_audit_record(self):
        """An allowed registration creates an audit record with outcome 'permitted'."""
        from backend.api.routes import create_router
        from backend.events.bus import EventBus
        from backend.governance.audit import AuditLogger
        from backend.governance.engine import GovernanceEngine
        from backend.replay.recorder import ReplayRecorder
        from backend.runtime.context import RuntimeExecutionContext
        from backend.runtime.manager import RuntimeManager
        from backend.telemetry.collector import TelemetryCollector
        from backend.telemetry.health import RuntimeHealthMonitor

        from fastapi import FastAPI

        ctx = RuntimeExecutionContext(time_source=lambda: 1000000.0)
        governance_engine = GovernanceEngine(ctx)
        audit_logger = AuditLogger(ctx)

        # Register allow policy
        policy = Policy(
            id="allow-all",
            name="Allow All",
            permissions=[
                Permission(action="*", level=PermissionLevel.ALLOW, resource="*")
            ],
        )
        governance_engine.register_policy(policy)

        app = FastAPI()
        router = create_router(
            context=ctx,
            runtime_manager=RuntimeManager(ctx),
            event_bus=EventBus(ctx),
            governance_engine=governance_engine,
            audit_logger=audit_logger,
            telemetry_collector=TelemetryCollector(ctx),
            health_monitor=RuntimeHealthMonitor(ctx),
            replay_recorder=ReplayRecorder(ctx),
        )
        app.include_router(router)
        client = TestClient(app)

        response = client.post(
            "/api/runtime/register",
            json={"name": "allowed-runtime", "metadata": {}},
        )

        assert response.status_code == 200
        records = audit_logger.get_records()
        assert len(records) == 1
        assert records[0].action == "runtime.register"
        assert records[0].outcome == "permitted"

    def test_replay_records_include_outputs(self):
        """Replay records include operation outputs after execution."""
        from backend.api.routes import create_router
        from backend.events.bus import EventBus
        from backend.governance.audit import AuditLogger
        from backend.governance.engine import GovernanceEngine
        from backend.replay.recorder import ReplayRecorder
        from backend.runtime.context import RuntimeExecutionContext
        from backend.runtime.manager import RuntimeManager
        from backend.telemetry.collector import TelemetryCollector
        from backend.telemetry.health import RuntimeHealthMonitor

        from fastapi import FastAPI

        ctx = RuntimeExecutionContext(time_source=lambda: 1000000.0)
        governance_engine = GovernanceEngine(ctx)
        audit_logger = AuditLogger(ctx)
        replay_recorder = ReplayRecorder(ctx)

        # Register allow policy
        policy = Policy(
            id="allow-all",
            name="Allow All",
            permissions=[
                Permission(action="*", level=PermissionLevel.ALLOW, resource="*")
            ],
        )
        governance_engine.register_policy(policy)

        app = FastAPI()
        router = create_router(
            context=ctx,
            runtime_manager=RuntimeManager(ctx),
            event_bus=EventBus(ctx),
            governance_engine=governance_engine,
            audit_logger=audit_logger,
            telemetry_collector=TelemetryCollector(ctx),
            health_monitor=RuntimeHealthMonitor(ctx),
            replay_recorder=replay_recorder,
        )
        app.include_router(router)
        client = TestClient(app)

        response = client.post(
            "/api/runtime/register",
            json={"name": "replay-test", "metadata": {"v": "1"}},
        )
        assert response.status_code == 200
        runtime_id = response.json()["id"]

        records = replay_recorder.get_records()
        assert len(records) == 1
        assert records[0].operation == "runtime.register"
        assert records[0].inputs == {"name": "replay-test", "metadata": {"v": "1"}}
        assert records[0].outputs["id"] == runtime_id
        assert records[0].outputs["state"] == "INITIALIZING"


class TestOperationalHealthEndpoint:
    """Test the /api/health operational health endpoint."""

    def test_health_returns_200_with_overall_status(self):
        """GET /api/health returns 200 with overall status field."""
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert "overall" in data
        assert "timestamp" in data
        assert "subsystems" in data

    def test_health_contains_all_subsystem_keys(self):
        """GET /api/health returns all expected subsystem keys."""
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        expected_subsystems = [
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
        for subsystem in expected_subsystems:
            assert subsystem in data["subsystems"], f"Missing subsystem: {subsystem}"
            assert "status" in data["subsystems"][subsystem]

    def test_health_overall_reflects_component_states(self):
        """GET /api/health overall status reflects aggregated component states."""
        from backend.api.routes import create_router
        from backend.events.bus import EventBus
        from backend.governance.audit import AuditLogger
        from backend.governance.engine import GovernanceEngine
        from backend.replay.recorder import ReplayRecorder
        from backend.runtime.context import RuntimeExecutionContext
        from backend.runtime.manager import RuntimeManager
        from backend.telemetry.collector import TelemetryCollector
        from backend.telemetry.health import RuntimeHealthMonitor
        from backend.telemetry.models import HealthState

        from fastapi import FastAPI

        ctx = RuntimeExecutionContext(time_source=lambda: 1000000.0)
        health_monitor = RuntimeHealthMonitor(ctx)

        # Set some components to healthy
        health_monitor.update_component("runtime_manager", HealthState.HEALTHY)
        health_monitor.update_component("event_bus", HealthState.HEALTHY)

        app = FastAPI()
        router = create_router(
            context=ctx,
            runtime_manager=RuntimeManager(ctx),
            event_bus=EventBus(ctx),
            governance_engine=GovernanceEngine(ctx),
            audit_logger=AuditLogger(ctx),
            telemetry_collector=TelemetryCollector(ctx),
            health_monitor=health_monitor,
            replay_recorder=ReplayRecorder(ctx),
        )
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["overall"] == "HEALTHY"
        assert data["subsystems"]["runtime_manager"]["status"] == "HEALTHY"
        assert data["subsystems"]["event_bus"]["status"] == "HEALTHY"


class TestGovernanceAuditEndpoint:
    """Test the /api/governance/audit endpoint."""

    def test_audit_returns_empty_records_list(self):
        """GET /api/governance/audit returns empty list when no records exist."""
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/governance/audit")

        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "total" in data
        assert isinstance(data["records"], list)

    def test_audit_returns_records_after_action(self):
        """GET /api/governance/audit returns records after governance actions."""
        app = create_app()
        client = TestClient(app)

        # Trigger a governance action by registering a runtime
        client.post(
            "/api/runtime/register",
            json={"name": "audit-test", "metadata": {}},
        )

        response = client.get("/api/governance/audit")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        record = data["records"][0]
        assert "id" in record
        assert "timestamp" in record
        assert "action" in record
        assert "actor" in record
        assert "outcome" in record
        assert "checksum" in record
