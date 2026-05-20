# NexusOS API Documentation

All endpoints are served from the FastAPI backend on port 8000. Every endpoint is prefixed with `/api`.

All mutating operations are validated by the GovernanceEngine before execution, recorded by the ReplayRecorder, and tracked by the TelemetryCollector.

---

## System

### GET /api/status

Returns the overall system status including component health.

**Response:**

```json
{
  "status": "operational",
  "timestamp": "2024-01-01T00:00:00.000000",
  "components": {
    "runtime_manager": {
      "runtime_count": 0
    },
    "event_bus": {
      "event_count": 0,
      "current_sequence": 0
    },
    "governance_engine": {
      "policy_count": 1,
      "active": true
    },
    "telemetry_collector": {
      "metric_count": 0,
      "trace_count": 0
    },
    "replay_recorder": {
      "record_count": 0,
      "current_sequence": 0
    }
  }
}
```

---

## Runtime Management

### POST /api/runtime/register

Register a new runtime instance. The operation is validated by the governance engine before execution.

**Request Body:**

```json
{
  "name": "my-runtime",
  "metadata": {
    "version": "1.0.0",
    "capabilities": ["execute", "observe"]
  }
}
```

**Response (200):**

```json
{
  "id": "rt-abc123",
  "name": "my-runtime",
  "state": "registered",
  "creation_timestamp": "2024-01-01T00:00:00.000000",
  "metadata": {
    "version": "1.0.0",
    "capabilities": ["execute", "observe"]
  }
}
```

**Response (403) - Governance Denied:**

```json
{
  "detail": "Action not permitted by governance policy"
}
```

---

### GET /api/runtime/{id}/status

Get the status of a specific registered runtime.

**Path Parameters:**

- `id` (string, required) - Runtime identifier

**Response (200):**

```json
{
  "id": "rt-abc123",
  "name": "my-runtime",
  "state": "registered",
  "creation_timestamp": "2024-01-01T00:00:00.000000",
  "metadata": {}
}
```

**Response (404):**

```json
{
  "detail": "Runtime not found"
}
```

---

## Events

### GET /api/events

List all recent events dispatched through the event bus.

**Response:**

```json
{
  "events": [
    {
      "id": "evt-001",
      "event_type": "RUNTIME",
      "data": {"action": "register", "name": "my-runtime"},
      "timestamp": "2024-01-01T00:00:00.000000",
      "sequence": 1
    }
  ],
  "total": 1
}
```

---

### GET /api/events/{id}

Get a specific event by its identifier.

**Path Parameters:**

- `id` (string, required) - Event identifier

**Response (200):**

```json
{
  "id": "evt-001",
  "event_type": "RUNTIME",
  "data": {"action": "register", "name": "my-runtime"},
  "timestamp": "2024-01-01T00:00:00.000000",
  "sequence": 1
}
```

**Response (404):**

```json
{
  "detail": "Event not found"
}
```

---

## Governance

### GET /api/governance/status

Get the governance engine status including all registered policies.

**Response:**

```json
{
  "active": true,
  "policy_count": 1,
  "policies": [
    {
      "id": "default-allow-all",
      "name": "Default Allow All",
      "active": true
    }
  ]
}
```

---

## Telemetry

### GET /api/telemetry/status

Get the telemetry collector status and current counters.

**Response:**

```json
{
  "metric_count": 5,
  "trace_count": 3,
  "counters": {
    "runtime.registrations": 2,
    "workflow.executions": 1
  }
}
```

---

### GET /api/telemetry/metrics

List all collected telemetry metrics.

**Response:**

```json
{
  "metrics": [
    {
      "id": "metric-001",
      "name": "runtime.registrations",
      "value": 2,
      "timestamp": "2024-01-01T00:00:00.000000",
      "labels": {}
    }
  ],
  "total": 1
}
```

---

### GET /api/telemetry/health

Get system health state for all components.

**Response:**

```json
{
  "overall": "healthy",
  "components": {
    "runtime_manager": "healthy",
    "event_bus": "healthy",
    "governance_engine": "healthy",
    "telemetry_collector": "healthy",
    "replay_recorder": "healthy",
    "browser_runtime": "healthy",
    "terminal_runtime": "healthy",
    "workflow_engine": "healthy",
    "skill_runtime": "healthy"
  }
}
```

---

### GET /api/telemetry/executions

Get execution telemetry metrics and health information.

**Response:**

```json
{
  "metrics": {
    "browser_traces": 5,
    "terminal_traces": 3,
    "workflow_traces": 2,
    "skill_traces": 1
  },
  "health": {
    "total_executions": 11,
    "status": "healthy"
  }
}
```

---

## Workflow

### POST /api/workflow/execute

Execute a workflow defined by a sequence of steps. Each step is governed and recorded.

**Request Body:**

```json
{
  "workflow_id": "wf-deploy-001",
  "name": "Deployment Workflow",
  "steps": [
    {
      "id": "step-1",
      "name": "Run Tests",
      "step_type": "TERMINAL",
      "config": {"command": "pytest"},
      "depends_on": []
    },
    {
      "id": "step-2",
      "name": "Build Image",
      "step_type": "TERMINAL",
      "config": {"command": "docker build ."},
      "depends_on": ["step-1"]
    }
  ]
}
```

**Step Types:** `BROWSER`, `TERMINAL`, `SKILL`, `CUSTOM`

**Response (200):**

```json
{
  "execution_id": "exec-001",
  "workflow_id": "wf-deploy-001",
  "state": "completed",
  "steps_completed": [
    {
      "step_id": "step-1",
      "status": "completed",
      "start_timestamp": "2024-01-01T00:00:00.000000",
      "end_timestamp": "2024-01-01T00:00:01.000000"
    }
  ]
}
```

**Response (403) - Governance Denied:**

```json
{
  "detail": "Workflow step type not permitted"
}
```

---

### GET /api/workflow/{id}/status

Get the status of a workflow execution.

**Path Parameters:**

- `id` (string, required) - Execution identifier

**Response (200):**

```json
{
  "execution_id": "exec-001",
  "workflow_id": "wf-deploy-001",
  "state": "completed",
  "steps_completed": 2,
  "current_step_id": null,
  "start_timestamp": "2024-01-01T00:00:00.000000",
  "end_timestamp": "2024-01-01T00:00:05.000000"
}
```

**Response (404):**

```json
{
  "detail": "Execution not found"
}
```

---

### GET /api/workflow/executions

List all workflow executions.

**Response:**

```json
{
  "executions": [
    {
      "id": "exec-001",
      "workflow_id": "wf-deploy-001",
      "state": "completed",
      "start_timestamp": "2024-01-01T00:00:00.000000"
    }
  ],
  "total": 1
}
```

---

## Browser

### POST /api/browser/start

Start a new browser session. The target URL is validated by the governance engine.

**Request Body:**

```json
{
  "url": "https://example.com"
}
```

**Response (200):**

```json
{
  "session_id": "bs-001",
  "url": "https://example.com",
  "state": "active",
  "creation_timestamp": "2024-01-01T00:00:00.000000"
}
```

**Response (403) - Governance Denied:**

```json
{
  "detail": "Browser target URL not permitted"
}
```

---

### GET /api/browser/sessions

List all browser sessions.

**Response:**

```json
{
  "sessions": [
    {
      "id": "bs-001",
      "url": "https://example.com",
      "state": "active",
      "creation_timestamp": "2024-01-01T00:00:00.000000"
    }
  ],
  "total": 1
}
```

---

### GET /api/browser/{id}/status

Get the status of a browser session.

**Path Parameters:**

- `id` (string, required) - Session identifier

**Response (200):**

```json
{
  "id": "bs-001",
  "url": "https://example.com",
  "state": "active",
  "screenshots": 2,
  "recording_length": 5
}
```

**Response (404):**

```json
{
  "detail": "Session not found"
}
```

---

### POST /api/browser/{id}/action

Execute an action within a browser session. The action target is validated by governance.

**Path Parameters:**

- `id` (string, required) - Session identifier

**Request Body:**

```json
{
  "action_type": "CLICK",
  "target": "#submit-button",
  "value": ""
}
```

**Action Types:** `CLICK`, `TYPE`, `NAVIGATE`, `SCREENSHOT`, `WAIT`

**Response (200):**

```json
{
  "session_id": "bs-001",
  "success": true,
  "action_type": "CLICK",
  "target": "#submit-button",
  "timestamp": "2024-01-01T00:00:00.000000",
  "error": null
}
```

**Response (403) - Governance Denied:**

```json
{
  "detail": "Browser action target not permitted"
}
```

**Response (404):**

```json
{
  "detail": "Session not found"
}
```

---

## Terminal

### POST /api/terminal/execute

Execute a terminal command. The command is validated by the governance engine before execution.

**Request Body:**

```json
{
  "session_id": "",
  "command": "echo hello",
  "working_dir": "/tmp",
  "timeout_seconds": 30
}
```

If `session_id` is empty, a new session is created automatically.

**Response (200):**

```json
{
  "session_id": "ts-001",
  "command": "echo hello",
  "stdout": "hello\n",
  "stderr": "",
  "exit_code": 0,
  "duration_ms": 15
}
```

**Response (403) - Governance Denied:**

```json
{
  "detail": "Terminal command not permitted"
}
```

---

### GET /api/terminal/{id}/status

Get the status of a terminal session.

**Path Parameters:**

- `id` (string, required) - Session identifier

**Response (200):**

```json
{
  "id": "ts-001",
  "state": "active",
  "command_count": 3,
  "creation_timestamp": "2024-01-01T00:00:00.000000"
}
```

**Response (404):**

```json
{
  "detail": "Session not found"
}
```

---

## Skills

### GET /api/skills

List all registered skills.

**Response:**

```json
{
  "skills": [
    {
      "id": "skill-summarize",
      "name": "Text Summarizer",
      "description": "Summarizes input text",
      "version": "1.0.0"
    }
  ],
  "total": 1
}
```

---

### POST /api/skills/invoke

Invoke a registered skill. The skill ID is validated against the governance engine and registered skills list.

**Request Body:**

```json
{
  "skill_id": "skill-summarize",
  "inputs": {
    "text": "Long text to summarize..."
  }
}
```

**Response (200):**

```json
{
  "skill_id": "skill-summarize",
  "outputs": {
    "summary": "Summarized text..."
  },
  "success": true,
  "duration_ms": 120,
  "error": null
}
```

**Response (403) - Governance Denied:**

```json
{
  "detail": "Skill invocation not permitted"
}
```

**Response (404):**

```json
{
  "detail": "Skill not found: skill-unknown"
}
```

---

## Replay

### GET /api/replay/{type}/{id}

Get replay records for a session. Replay data contains the full input/output trace for deterministic replay.

**Path Parameters:**

- `type` (string, required) - Session type: `browser`, `terminal`, or `workflow`
- `id` (string, required) - Session or execution identifier

**Response (200):**

```json
{
  "session_type": "terminal",
  "session_id": "ts-001",
  "records": [
    {
      "command": "echo hello",
      "exit_code": 0,
      "stdout": "hello\n"
    }
  ],
  "total": 1
}
```

**Response (400):**

```json
{
  "detail": "Invalid session type: unknown"
}
```

**Response (404):**

```json
{
  "detail": "Replay data not found"
}
```
