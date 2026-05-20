# Troubleshooting Guide

Common issues and their solutions when running NexusOS.

## Startup Failures

### Missing Python dependencies

**Symptom:** `ModuleNotFoundError` on startup.

**Fix:** Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

### Wrong Python version

**Symptom:** Syntax errors or type hint failures on startup.

**Fix:** NexusOS requires Python 3.11+. Check your version:

```bash
python --version
```

### Port 8000 already in use

**Symptom:** `[Errno 98] Address already in use` or `[Errno 48] Address already in use`.

**Fix:** Either stop the process using port 8000 or run on a different port:

```bash
# Find what is using port 8000
lsof -i :8000

# Run on a different port
uvicorn backend.main:app --port 8001
```

### Import errors from backend modules

**Symptom:** `ModuleNotFoundError: No module named 'backend'`.

**Fix:** Run from the project root directory, or install the project in development mode. The `backend` package must be importable from the working directory:

```bash
# Run from project root
uvicorn backend.main:app --reload
```

## Docker Issues

### Build failures

**Symptom:** `docker build` fails with dependency errors.

**Fix:** Ensure the Dockerfile context is the project root:

```bash
docker build -t nexusos .
```

If a Python package fails to install, check that `backend/requirements.txt` is up to date and that the base image has the correct Python version.

### Container networking

**Symptom:** Frontend cannot reach the backend container.

**Fix:** When using `docker-compose`, services communicate by service name. Ensure:

1. Both services are on the same Docker network (docker-compose handles this automatically).
2. The frontend uses the service name (e.g., `http://backend:8000`) not `localhost`.
3. Port mappings in `docker-compose.yml` expose the correct ports to the host.

### docker-compose fails to start

**Symptom:** `docker-compose up` exits immediately or services restart in a loop.

**Fix:**

1. Check logs: `docker-compose logs backend`
2. Verify `.env` file exists (copy from `.env.example` if needed)
3. Ensure required environment variables are set

## API Errors

### 403 Forbidden - Governance Denial

**Symptom:** API returns HTTP 403 with a message like "Denied by policy: ..." or "No policy permits this action (default deny)".

**Cause:** The governance engine denied the action. This happens when:
- No policy grants ALLOW for the attempted action
- A policy explicitly has a DENY permission matching the action

**Debug steps:**

1. Check the audit trail for denial details:

```bash
curl http://localhost:8000/api/governance/audit
```

2. Check which policies are active:

```bash
curl http://localhost:8000/api/governance/status
```

3. If no policies are registered, the system defaults to deny-all. Register a permissive policy for development (see Governance section below).

### 403 from Execution Governance Validator

**Symptom:** 403 with messages like "Blocked URL scheme: file://", "Blocked dangerous command: shutdown", or "Workflow exceeds maximum step count".

**Cause:** The `ExecutionGovernanceValidator` enforces hard safety constraints that cannot be overridden by policies:

- Browser: `file://` and `javascript:` URLs are always blocked
- Terminal: `rm -rf /`, `shutdown`, `reboot`, `mkfs` are always blocked
- Workflow: Maximum 100 steps, only valid step types (BROWSER, TERMINAL, SKILL, CUSTOM)
- Skills: Skill must be registered before invocation

These are safety rails, not policy decisions. They cannot be bypassed.

### 404 Not Found

**Symptom:** API returns HTTP 404.

**Common causes:**

- **Runtime/session not found:** The session ID does not exist. Sessions are created on-demand; ensure you called the creation endpoint first (e.g., `POST /api/browser/start`).
- **Execution not found:** The execution ID from a workflow is invalid or was never created.
- **Wrong URL path:** Check the endpoint path. All API routes are prefixed with `/api/`.

### Validation Errors (422)

**Symptom:** API returns HTTP 422 Unprocessable Entity.

**Cause:** The request body does not match the expected schema. Check:

- Required fields are present
- Field types match (strings vs numbers vs objects)
- Enum values are valid (e.g., step_type must be BROWSER, TERMINAL, SKILL, or CUSTOM)

## Governance Denial Debugging

### How to check the audit trail

The audit trail records every governance decision:

```bash
curl -s http://localhost:8000/api/governance/audit | python -m json.tool
```

Look for records with `"outcome": "denied"`. The `metadata` field contains the denial reason and the policy that caused it.

### How to add a permissive development policy

If the system is denying all actions because no policy is registered:

```bash
curl -X POST http://localhost:8000/api/governance/policies \
  -H "Content-Type: application/json" \
  -d '{
    "id": "dev-allow-all",
    "name": "Development Allow All",
    "permissions": [{"action": "*", "level": "ALLOW", "resource": "*"}],
    "active": true
  }'
```

The default application startup in `backend/main.py` already registers a "Default Allow All" policy. If you are seeing denials, either:
- The default policy was removed at runtime
- A more specific DENY policy was registered and takes precedence
- The action is blocked by the ExecutionGovernanceValidator (hard safety constraints)

### Policy evaluation order

Policies are evaluated in registration order. The first matching permission wins. If a DENY is matched before an ALLOW, the action is denied. Reorder or restructure policies accordingly.

## Frontend Connection Issues

### CORS errors in browser console

**Symptom:** Browser console shows "Access to fetch has been blocked by CORS policy".

**Cause:** The backend's CORS configuration does not include the frontend's origin.

**Fix:** Set the `NEXUSOS_CORS_ORIGINS` environment variable to include the frontend origin:

```bash
# Allow the default Next.js dev server
export NEXUSOS_CORS_ORIGINS="http://localhost:3000"

# Allow multiple origins (comma-separated)
export NEXUSOS_CORS_ORIGINS="http://localhost:3000,https://app.example.com"
```

The default value is `"*"` (allow all origins) which works for local development. The CORS middleware is configured in `backend/main.py`.

### Next.js proxy rewrite not working

**Symptom:** Frontend API calls return 404 or connection refused.

**Cause:** The Next.js rewrite proxy in `next.config.js` may not be pointing to the correct backend URL.

**Fix:** Ensure `NEXT_PUBLIC_API_BASE_URL` is set correctly:

```bash
# For local development
export NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
```

The frontend API client at `frontend/lib/api.ts` uses this variable to construct request URLs.

### Frontend build failures

**Symptom:** `npm run build` fails in the frontend directory.

**Fix:**

```bash
cd frontend
npm install
npm run build
```

Ensure Node.js v22 is installed. Check for TypeScript errors in the build output.

## Health and Telemetry

### Checking system health

Use the health endpoint to verify all subsystems are running:

```bash
curl http://localhost:8000/api/health
```

Expected response when healthy:

```json
{
  "overall": "HEALTHY",
  "timestamp": "...",
  "subsystems": {
    "runtime_manager": {"status": "HEALTHY"},
    "event_bus": {"status": "HEALTHY"},
    "governance_engine": {"status": "HEALTHY"},
    "telemetry_collector": {"status": "HEALTHY"},
    "replay_recorder": {"status": "HEALTHY"},
    "browser_runtime": {"status": "HEALTHY"},
    "terminal_runtime": {"status": "HEALTHY"},
    "workflow_engine": {"status": "HEALTHY"},
    "skill_runtime": {"status": "HEALTHY"}
  }
}
```

If any subsystem shows a non-HEALTHY status, check the application logs for errors during initialization.
