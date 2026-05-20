"""Tests for execution API endpoints."""

from fastapi.testclient import TestClient

from backend.main import create_app
from backend.skills.models import SkillDefinition


def make_client() -> TestClient:
    """Create a test client with a fresh app instance."""
    app = create_app()
    return TestClient(app)


class TestWorkflowEndpoints:
    """Test workflow execution API endpoints."""

    def test_execute_workflow(self):
        """Can execute a workflow via API."""
        client = make_client()

        response = client.post(
            "/api/workflow/execute",
            json={
                "name": "Test Workflow",
                "steps": [
                    {"id": "s1", "name": "Step 1", "step_type": "TERMINAL"},
                    {"id": "s2", "name": "Step 2", "step_type": "BROWSER"},
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "COMPLETED"
        assert len(data["steps_completed"]) == 2

    def test_execute_workflow_governance_blocks_invalid_type(self):
        """Workflow with invalid step type is blocked by governance."""
        client = make_client()

        response = client.post(
            "/api/workflow/execute",
            json={
                "name": "Bad Workflow",
                "steps": [{"id": "s1", "name": "Bad", "step_type": "INVALID"}],
            },
        )

        assert response.status_code == 403

    def test_get_workflow_executions(self):
        """Can list workflow executions."""
        client = make_client()

        # Execute a workflow first
        client.post(
            "/api/workflow/execute",
            json={
                "name": "Test",
                "steps": [{"id": "s1", "name": "S1", "step_type": "TERMINAL"}],
            },
        )

        response = client.get("/api/workflow/executions")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    def test_get_workflow_status(self):
        """Can get a specific workflow execution status."""
        client = make_client()

        exec_response = client.post(
            "/api/workflow/execute",
            json={
                "name": "Status Test",
                "steps": [{"id": "s1", "name": "S1", "step_type": "SKILL"}],
            },
        )
        execution_id = exec_response.json()["execution_id"]

        response = client.get(f"/api/workflow/{execution_id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == execution_id
        assert data["state"] == "COMPLETED"

    def test_get_workflow_status_not_found(self):
        """Getting a nonexistent execution returns 404."""
        client = make_client()

        response = client.get("/api/workflow/nonexistent/status")

        assert response.status_code == 404


class TestBrowserEndpoints:
    """Test browser session API endpoints."""

    def test_list_browser_sessions_empty(self):
        """Initially no browser sessions exist."""
        client = make_client()

        response = client.get("/api/browser/sessions")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_get_browser_status_not_found(self):
        """Getting a nonexistent browser session returns 404."""
        client = make_client()

        response = client.get("/api/browser/nonexistent/status")

        assert response.status_code == 404

    def test_browser_action_governance_blocks_file_url(self):
        """Browser action with file:// URL is blocked by governance."""
        client = make_client()

        # Start a session first
        start_response = client.post(
            "/api/browser/start",
            json={"url": "https://example.com"},
        )
        assert start_response.status_code == 200
        session_id = start_response.json()["session_id"]

        # Attempt action with file:// target
        response = client.post(
            f"/api/browser/{session_id}/action",
            json={
                "action_type": "NAVIGATE",
                "target": "file:///etc/passwd",
                "value": "",
            },
        )

        assert response.status_code == 403

    def test_browser_start_governance_blocks_file_url(self):
        """Starting a browser session with file:// URL is blocked by governance."""
        client = make_client()

        response = client.post(
            "/api/browser/start",
            json={"url": "file:///etc/passwd"},
        )

        assert response.status_code == 403

    def test_browser_action_succeeds_with_valid_url(self):
        """Browser action with valid HTTPS URL succeeds."""
        client = make_client()

        # Start a session
        start_response = client.post(
            "/api/browser/start",
            json={"url": "https://example.com"},
        )
        assert start_response.status_code == 200
        session_id = start_response.json()["session_id"]

        # Execute a valid action
        response = client.post(
            f"/api/browser/{session_id}/action",
            json={
                "action_type": "NAVIGATE",
                "target": "https://example.com/page",
                "value": "",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestTerminalEndpoints:
    """Test terminal execution API endpoints."""

    def test_execute_terminal_command(self):
        """Can execute a terminal command via API."""
        client = make_client()

        response = client.post(
            "/api/terminal/execute",
            json={"command": "echo hello"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["stdout"].strip() == "hello"
        assert data["exit_code"] == 0

    def test_execute_terminal_blocked_command(self):
        """Dangerous commands are blocked by governance."""
        client = make_client()

        response = client.post(
            "/api/terminal/execute",
            json={"command": "rm -rf /"},
        )

        assert response.status_code == 403

    def test_get_terminal_status(self):
        """Can get terminal session status after execution."""
        client = make_client()

        exec_response = client.post(
            "/api/terminal/execute",
            json={"command": "echo test"},
        )
        session_id = exec_response.json()["session_id"]

        response = client.get(f"/api/terminal/{session_id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["command_count"] == 1

    def test_get_terminal_status_not_found(self):
        """Getting a nonexistent terminal session returns 404."""
        client = make_client()

        response = client.get("/api/terminal/nonexistent/status")

        assert response.status_code == 404


class TestSkillEndpoints:
    """Test skill API endpoints."""

    def test_list_skills_empty(self):
        """Initially no skills are registered."""
        client = make_client()

        response = client.get("/api/skills")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_invoke_unregistered_skill_blocked(self):
        """Invoking an unregistered skill is blocked by governance."""
        client = make_client()

        response = client.post(
            "/api/skills/invoke",
            json={"skill_id": "nonexistent", "inputs": {}},
        )

        assert response.status_code == 403


class TestReplayEndpoints:
    """Test replay API endpoints."""

    def test_get_replay_after_terminal_execution(self):
        """Replay data exists after terminal command execution."""
        client = make_client()

        exec_response = client.post(
            "/api/terminal/execute",
            json={"command": "echo replay_test"},
        )
        session_id = exec_response.json()["session_id"]

        response = client.get(f"/api/replay/terminal/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["session_type"] == "terminal"
        assert data["total"] >= 1

    def test_get_replay_not_found(self):
        """Getting replay for nonexistent session returns 404."""
        client = make_client()

        response = client.get("/api/replay/browser/nonexistent")

        assert response.status_code == 404

    def test_get_replay_invalid_type(self):
        """Invalid session type returns 400."""
        client = make_client()

        response = client.get("/api/replay/invalid/session-1")

        assert response.status_code == 400


class TestTelemetryEndpoints:
    """Test telemetry API endpoints."""

    def test_get_execution_telemetry(self):
        """Can get execution telemetry metrics."""
        client = make_client()

        response = client.get("/api/telemetry/executions")

        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "health" in data

    def test_telemetry_updates_after_execution(self):
        """Telemetry updates after executing commands."""
        client = make_client()

        client.post("/api/terminal/execute", json={"command": "echo hi"})

        response = client.get("/api/telemetry/executions")
        data = response.json()
        assert data["metrics"]["counters"]["terminal_commands"] >= 1
