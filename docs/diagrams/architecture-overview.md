# NexusOS Architecture Overview

## System Architecture

```
+------------------------------------------+
|           NexusOS Platform               |
+------------------------------------------+
|  Frontend (Next.js Dashboard)            |
|  - System Health    - Execution Control  |
|  - Governance View  - Replay Inspector   |
+------------------------------------------+
           |  HTTP/REST API  |
+------------------------------------------+
|           API Layer (FastAPI)             |
|  - Routes          - Execution Routes    |
|  - OpenAPI Schema  - CORS Middleware     |
+------------------------------------------+
           |                |
+----------v---+    +------v-----------+
| Governance   |    | Runtime Manager   |
| Engine       |    |                   |
| - Policies   |    | - Browser Runtime |
| - Validation |    | - Terminal Runtime |
| - Audit Log  |    | - Skill Runtime   |
+--------------+    | - Workflow Engine  |
                    +-------------------+
           |                |
+----------v---+    +------v-----------+
| Observability|    | Replay System     |
| - Telemetry  |    | - Recorder        |
| - Health Mon |    | - Loader          |
| - Event Bus  |    | - Execution Mgr   |
+--------------+    +-------------------+
```

## Component Relationships

```
+-------------------+
| RuntimeExecution  |
| Context           |
+--------+----------+
         |
         | injected into
         v
+--------+----------+     +------------------+
| GovernanceEngine  |<--->| AuditLogger      |
| (validates all    |     | (records all     |
|  operations)      |     |  decisions)      |
+--------+----------+     +------------------+
         |
         | authorizes
         v
+--------+----------+     +------------------+
| RuntimeManager    |---->| EventBus         |
| (dispatches to    |     | (publishes       |
|  runtimes)        |     |  events)         |
+--------+----------+     +------------------+
         |
         | executes via
         v
+--------+---+---+---+---+--+
|            |   |   |      |
v            v   v   v      v
Browser  Terminal Skill  Workflow
Runtime  Runtime  Runtime Engine
         |
         | recorded by
         v
+--------+----------+     +------------------+
| ReplayRecorder    |     | TelemetryCollector|
| (captures ops     |     | (tracks metrics, |
|  for replay)      |     |  health status)  |
+-------------------+     +------------------+
```

## Data Flow

```
Request --> API Layer --> Governance Engine --> Runtime Manager
                              |                      |
                              v                      v
                         Audit Log            Execute Action
                                                    |
                                                    v
                                              EventBus (emit)
                                                    |
                                         +----------+----------+
                                         |          |          |
                                         v          v          v
                                     Telemetry   Replay    Response
                                     Collector   Recorder  to Client
```

## Module Boundaries

| Module | Responsibility | Interface |
|--------|---------------|-----------|
| `backend/api/` | HTTP request handling, routing | FastAPI routes |
| `backend/governance/` | Policy evaluation, audit logging | GovernanceEngine, AuditLogger |
| `backend/runtime/` | Runtime registration, dispatch | RuntimeManager |
| `backend/browser/` | Browser automation execution | BrowserRuntime |
| `backend/terminal/` | Command execution | TerminalRuntime |
| `backend/skills/` | Skill registration and invocation | SkillRuntime |
| `backend/workflow/` | DAG-based workflow orchestration | WorkflowEngine |
| `backend/events/` | Event publication and subscription | EventBus |
| `backend/telemetry/` | Metrics collection, health monitoring | TelemetryCollector |
| `backend/replay/` | Operation recording and replay | ReplayRecorder, ReplayLoader |
