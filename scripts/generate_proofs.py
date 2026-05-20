"""Generate proof artifacts by exercising all major NexusOS API endpoints.

Uses httpx TestClient with the real FastAPI application from backend.main.
Each proof artifact contains: timestamp, endpoint called, response data,
and a SHA256 checksum of the response body for tamper evidence.
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

from starlette.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.main import create_app

PROOF_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "proofs",
    "final-productization",
)


def make_proof(endpoint: str, method: str, response_data: dict, status_code: int) -> dict:
    """Create a proof artifact with timestamp and checksum."""
    response_body = json.dumps(response_data, sort_keys=True, default=str)
    checksum = hashlib.sha256(response_body.encode()).hexdigest()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "response_data": response_data,
        "response_body_sha256": checksum,
    }


def save_proof(filename: str, proof: dict) -> None:
    """Save proof artifact to file."""
    filepath = os.path.join(PROOF_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(proof, f, indent=2, default=str)
    print(f"  Saved: {filename}")


def main():
    """Generate all proof artifacts."""
    os.makedirs(PROOF_DIR, exist_ok=True)

    app = create_app()

    with TestClient(app) as client:
        # a) GET /api/status
        print("[1/10] GET /api/status")
        resp = client.get("/api/status")
        proof = make_proof("/api/status", "GET", resp.json(), resp.status_code)
        save_proof("api-status-proof.json", proof)

        # b) POST /api/runtime/register
        print("[2/10] POST /api/runtime/register")
        resp = client.post(
            "/api/runtime/register",
            json={"name": "proof-runtime", "metadata": {"type": "verification"}},
        )
        proof = make_proof("/api/runtime/register", "POST", resp.json(), resp.status_code)
        save_proof("runtime-registration-proof.json", proof)

        # c) GET /api/governance/status
        print("[3/10] GET /api/governance/status")
        resp = client.get("/api/governance/status")
        proof = make_proof("/api/governance/status", "GET", resp.json(), resp.status_code)
        save_proof("governance-proof.json", proof)

        # d) POST /api/workflow/execute (2-step workflow)
        print("[4/10] POST /api/workflow/execute")
        resp = client.post(
            "/api/workflow/execute",
            json={
                "workflow_id": "proof-workflow-001",
                "name": "Verification Workflow",
                "steps": [
                    {
                        "id": "step-1",
                        "name": "Initialize",
                        "step_type": "CUSTOM",
                        "config": {"action": "init"},
                        "depends_on": [],
                    },
                    {
                        "id": "step-2",
                        "name": "Process",
                        "step_type": "CUSTOM",
                        "config": {"action": "process"},
                        "depends_on": ["step-1"],
                    },
                ],
            },
        )
        proof = make_proof("/api/workflow/execute", "POST", resp.json(), resp.status_code)
        save_proof("workflow-execution-proof.json", proof)

        # e) POST /api/browser/start
        print("[5/10] POST /api/browser/start")
        resp = client.post(
            "/api/browser/start",
            json={"url": "https://example.com"},
        )
        proof = make_proof("/api/browser/start", "POST", resp.json(), resp.status_code)
        save_proof("browser-session-proof.json", proof)

        # f) POST /api/terminal/execute
        print("[6/10] POST /api/terminal/execute")
        resp = client.post(
            "/api/terminal/execute",
            json={"command": "echo NexusOS Verification"},
        )
        terminal_data = resp.json()
        proof = make_proof("/api/terminal/execute", "POST", terminal_data, resp.status_code)
        save_proof("terminal-execution-proof.json", proof)

        # Extract session_id for replay
        terminal_session_id = terminal_data.get("session_id", "")

        # g) GET /api/telemetry/executions
        print("[7/10] GET /api/telemetry/executions")
        resp = client.get("/api/telemetry/executions")
        proof = make_proof("/api/telemetry/executions", "GET", resp.json(), resp.status_code)
        save_proof("telemetry-proof.json", proof)

        # h) GET /api/replay/terminal/{session_id}
        print(f"[8/10] GET /api/replay/terminal/{terminal_session_id}")
        resp = client.get(f"/api/replay/terminal/{terminal_session_id}")
        proof = make_proof(
            f"/api/replay/terminal/{terminal_session_id}",
            "GET",
            resp.json(),
            resp.status_code,
        )
        save_proof("replay-proof.json", proof)

        # i) GET /api/telemetry/health
        print("[9/10] GET /api/telemetry/health")
        resp = client.get("/api/telemetry/health")
        proof = make_proof("/api/telemetry/health", "GET", resp.json(), resp.status_code)
        save_proof("health-proof.json", proof)

        # j) GET /api/openapi
        print("[10/10] GET /api/openapi")
        resp = client.get("/api/openapi")
        proof = make_proof("/api/openapi", "GET", resp.json(), resp.status_code)
        save_proof("openapi-schema-proof.json", proof)

    print("\nAll proof artifacts generated successfully.")


if __name__ == "__main__":
    main()
