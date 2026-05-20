# Runtime Execution Guide

NexusOS provides four runtime types for executing actions. Each runtime is governed: every action passes through the `ExecutionGovernanceValidator` before execution. This guide covers each runtime's purpose, API endpoints, governance constraints, and usage examples.

All execution endpoints are defined in `backend/api/execution_routes.py` and prefixed with `/api`.

## Browser Runtime

**Source:** `backend/browser/runtime.py`

The Browser Runtime manages browser sessions for navigation and page interaction. It wraps session lifecycle and action execution with deterministic timestamps.

### Capabilities

- Start browser sessions with an initial URL
- Execute actions within sessions (navigate, click, extract, screenshot)
- Capture screenshots of session state
- List and inspect sessions

### API Endpoints

| Method | Path                              | Description                    |
|--------|-----------------------------------|--------------------------------|
| POST   | `/api/browser/start`              | Start a new browser session    |
| POST   | `/api/browser/{session_id}/action`| Execute an action in a session |
| GET    | `/api/browser/sessions`           | List all browser sessions      |
| GET    | `/api/browser/{session_id}/status`| Get session status             |

### Governance Checks

Before any browser action executes, the `ExecutionGovernanceValidator.validate_browser_action` method checks the target URL:

- **Blocked:** `file://` and `javascript:` URL schemes
- **Permitted:** All other URLs

These are hard safety constraints that cannot be overridden by policy.

### Example: Start a Session

**Request:**

```bash
curl -X POST http://localhost:8000/api/browser/start \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

**Response:**

```json
{
  "session_id": "a1b2c3d4e5f6g7h8",
  "url": "https://example.com",
  "state": "ACTIVE",
  "creation_timestamp": "2025-01-18T10:00:00Z"
}
```

### Example: Execute a Browser Action

**Request:**

```bash
curl -X POST http://localhost:8000/api/browser/a1b2c3d4e5f6g7h8/action \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "NAVIGATE",
    "target": "https://example.com/page",
    "selector": ""
  }'
```

**Response:**

```json
{
  "session_id": "a1b2c3d4e5f6g7h8",
  "success": true,
  "action_type": "NAVIGATE",
  "target": "https://example.com/page",
  "timestamp": "2025-01-18T10:00:01Z",
  "error": null
}
```

---

## Terminal Runtime

**Source:** `backend/terminal/runtime.py`

The Terminal Runtime executes shell commands within managed sessions. Commands run via `subprocess.run` with timeout enforcement and stdout/stderr capture.

### Capabilities

- Create terminal sessions
- Execute commands with configurable working directory and timeout
- Capture stdout, stderr, and exit codes
- Track command history per session

### API Endpoints

| Method | Path                                | Description                      |
|--------|-------------------------------------|----------------------------------|
| POST   | `/api/terminal/execute`             | Execute a terminal command       |
| GET    | `/api/terminal/{session_id}/status` | Get terminal session status      |

### Governance Checks

Before any command executes, `ExecutionGovernanceValidator.validate_terminal_command` checks the command string against blocklists:

- **Blocked commands:** `shutdown`, `reboot`, `mkfs`
- **Blocked patterns:** `rm -rf /` (targeting root specifically; `rm -rf /some/path` is allowed)

These are hard safety constraints that cannot be overridden by policy.

### Example: Execute a Command

**Request:**

```bash
curl -X POST http://localhost:8000/api/terminal/execute \
  -H "Content-Type: application/json" \
  -d '{
    "command": "ls -la /tmp",
    "working_dir": "/tmp",
    "timeout_seconds": 10
  }'
```

**Response:**

```json
{
  "session_id": "b2c3d4e5f6g7h8i9",
  "command": "ls -la /tmp",
  "stdout": "total 0\ndrwxrwxrwt 2 root root 40 Jan 18 10:00 .\n",
  "stderr": "",
  "exit_code": 0,
  "duration_ms": 12.5
}
```

If `session_id` is omitted from the request, a new session is created automatically.

### Example: Governance Denial

**Request:**

```bash
curl -X POST http://localhost:8000/api/terminal/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "shutdown -h now"}'
```

**Response (403):**

```json
{
  "detail": "Blocked dangerous command: shutdown"
}
```

---

## Workflow Runtime

**Source:** `backend/workflow/engine.py`

The Workflow Engine orchestrates multi-step workflows with dependency-based ordering. Steps are executed sequentially respecting `depends_on` relationships via topological sort.

### Capabilities

- Define workflows with typed steps (BROWSER, TERMINAL, SKILL, CUSTOM)
- Execute workflows with dependency resolution
- Track execution state (RUNNING, COMPLETED, FAILED)
- List workflow definitions and executions

### API Endpoints

| Method | Path                                    | Description                      |
|--------|-----------------------------------------|----------------------------------|
| POST   | `/api/workflow/execute`                 | Execute a workflow               |
| GET    | `/api/workflow/{execution_id}/status`   | Get execution status             |
| GET    | `/api/workflow/executions`              | List all executions              |

### Governance Checks

Before workflow execution, `ExecutionGovernanceValidator.validate_workflow_execution` validates:

- **Step count:** Maximum 100 steps per workflow
- **Step types:** Must be one of `BROWSER`, `TERMINAL`, `SKILL`, `CUSTOM`

Invalid step types or excessive step counts result in a 403 denial.

### Example: Execute a Workflow

**Request:**

```bash
curl -X POST http://localhost:8000/api/workflow/execute \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Setup Environment",
    "steps": [
      {
        "id": "step-1",
        "name": "Create directory",
        "step_type": "TERMINAL",
        "config": {"command": "mkdir -p /tmp/workspace"}
      },
      {
        "id": "step-2",
        "name": "Open browser",
        "step_type": "BROWSER",
        "config": {"url": "https://example.com"},
        "depends_on": ["step-1"]
      }
    ]
  }'
```

**Response:**

```json
{
  "execution_id": "c3d4e5f6g7h8i9j0",
  "workflow_id": "wf-2025-01-18T10:00:00Z",
  "state": "COMPLETED",
  "steps_completed": [
    {"step_id": "step-1", "status": "success", "outputs": {}, "duration_ms": 0.0, "error": null},
    {"step_id": "step-2", "status": "success", "outputs": {}, "duration_ms": 0.0, "error": null}
  ]
}
```

### Example: Check Execution Status

```bash
curl http://localhost:8000/api/workflow/c3d4e5f6g7h8i9j0/status
```

**Response:**

```json
{
  "execution_id": "c3d4e5f6g7h8i9j0",
  "workflow_id": "wf-2025-01-18T10:00:00Z",
  "state": "COMPLETED",
  "steps_completed": 2,
  "current_step_id": null,
  "start_timestamp": "2025-01-18T10:00:00Z",
  "end_timestamp": "2025-01-18T10:00:01Z"
}
```

---

## Skills Runtime

**Source:** `backend/skills/runtime.py`

The Skills Runtime manages modular typed plugins. Skills are registered with a definition and an optional handler function, then invoked by ID with typed inputs.

### Capabilities

- Register skills with definitions and handler functions
- Invoke skills by ID with typed inputs
- List all registered skills
- Track invocation results and duration

### API Endpoints

| Method | Path                   | Description                     |
|--------|------------------------|---------------------------------|
| GET    | `/api/skills`          | List all registered skills      |
| POST   | `/api/skills/invoke`   | Invoke a registered skill       |

### Governance Checks

Before skill invocation, `ExecutionGovernanceValidator.validate_skill_invocation` validates:

- **Skill must be registered:** The `skill_id` must exist in the skill registry
- Unregistered skill IDs are denied with a 403

### Example: List Skills

```bash
curl http://localhost:8000/api/skills
```

**Response:**

```json
{
  "skills": [
    {
      "id": "summarize-text",
      "name": "Text Summarizer",
      "description": "Summarizes input text",
      "version": "1.0.0"
    }
  ],
  "total": 1
}
```

### Example: Invoke a Skill

**Request:**

```bash
curl -X POST http://localhost:8000/api/skills/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "summarize-text",
    "inputs": {"text": "Long document content here..."}
  }'
```

**Response:**

```json
{
  "skill_id": "summarize-text",
  "outputs": {},
  "success": true,
  "duration_ms": 1.2,
  "error": null
}
```

### Example: Governance Denial (Unregistered Skill)

**Request:**

```bash
curl -X POST http://localhost:8000/api/skills/invoke \
  -H "Content-Type: application/json" \
  -d '{"skill_id": "nonexistent-skill", "inputs": {}}'
```

**Response (403):**

```json
{
  "detail": "Skill not registered: nonexistent-skill"
}
```

---

## Replay and Telemetry

All runtime actions are automatically recorded for replay and telemetry:

- **Replay:** `GET /api/replay/{session_type}/{session_id}` retrieves the recorded actions for browser, terminal, or workflow sessions.
- **Telemetry:** `GET /api/telemetry/executions` returns execution metrics and health across all runtimes.

These systems operate transparently alongside governance and do not affect action execution.
