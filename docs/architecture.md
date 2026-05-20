# NexusOS Architecture

This document describes the architecture of NexusOS, its component relationships, and the design principles that govern the system.

---

## Design Principles

1. **Governance-First** - All behavior is governed. No uncontrolled execution exists.
2. **Deterministic** - Same inputs always produce the same outputs.
3. **Replayable** - All operations are recorded and can be replayed exactly.
4. **Observable** - Every action is traceable, measurable, and auditable.
5. **Modular** - Independent, composable components with explicit interfaces.

---

## System Overview

```
+------------------------------------------------------------------+
|                      NexusOS Platform                              |
+------------------------------------------------------------------+
|                                                                    |
|  +------------------+         +---------------------------+       |
|  | Next.js Frontend | ------> | FastAPI Backend (Port 8000)|      |
|  | (Port 3000)      |  HTTP   |                           |       |
|  +------------------+         +---------------------------+       |
|                                         |                          |
|                                         v                          |
|                    +-------------------------------------+         |
|                    |    RuntimeExecutionContext           |         |
|                    |  (Deterministic time, shared state)  |         |
|                    +-------------------------------------+         |
|                         |    |    |    |    |    |                  |
+------------------------------------------------------------------+
```

---

## Core Components

### RuntimeExecutionContext

The foundation of all operations. Provides:
- Deterministic time source (injectable for testing and replay)
- Shared execution state visible to all components
- Context propagation across component boundaries

```
                 RuntimeExecutionContext
                         |
         +-------+-------+-------+-------+
         |       |       |       |       |
         v       v       v       v       v
     Governance Event  Telemetry Replay Runtime
      Engine    Bus   Collector Recorder Manager
```

### GovernanceEngine

Validates every operation before execution:

```
  Incoming Request
         |
         v
  +----------------+
  | GovernanceEngine|
  |                |
  | - Policy Store |
  | - Validator    |
  +----------------+
         |
    +----+----+
    |         |
    v         v
 PERMIT     DENY
    |         |
    v         v
 Execute   Return 403
 + Audit   + Audit
```

- Maintains a policy store with active/inactive policies
- Each policy contains permissions (action + resource + level)
- All validation results are audited (both permitted and denied)
- Governance mode (strict/permissive) affects default behavior

### EventBus

Dispatches events across the system:

```
  Producer (any component)
         |
         v
  +-------------+
  |  EventBus   |
  | - Sequence  |
  | - History   |
  +-------------+
         |
         v
  Event Storage (queryable via API)
```

- Sequential event numbering for ordering guarantees
- Event types: RUNTIME, GOVERNANCE, TELEMETRY, EXECUTION
- Full event history accessible via API

### TelemetryCollector

Tracks metrics and traces for all operations:

```
  +-------------------+
  | TelemetryCollector |
  +-------------------+
  | - Counters        |
  | - Metrics         |
  | - Traces          |
  +-------------------+
         |
         v
  +-------------------+
  | RuntimeHealthMonitor|
  +-------------------+
  | - Component states |
  | - Overall health   |
  +-------------------+
```

- Counter-based metrics (incrementable)
- Named metric records with labels
- Per-component health state tracking
- Overall system health aggregation

### ReplayRecorder

Captures all operations for deterministic replay:

```
  Operation Execution
         |
         v
  +----------------+
  | ReplayRecorder |
  | - Inputs       |
  | - Outputs      |
  | - Sequence     |
  +----------------+
         |
         v
  Replay Storage (queryable via API)
```

- Records inputs and outputs for every operation
- Sequential numbering for replay ordering
- Supports replay by operation type and ID

---

## Execution Runtimes

### Browser Runtime

```
  POST /api/browser/start
         |
         v
  +--------------------+     +-------------------------+
  | GovernanceValidator |---->| ExecutionGovernance     |
  +--------------------+     | (URL validation)        |
         |                   +-------------------------+
         v
  +--------------------+
  | BrowserRuntime     |
  | - Session Store    |
  | - Action Executor  |
  | - Screenshot Cap.  |
  +--------------------+
         |
    +----+----+
    |         |
    v         v
  Telemetry  Replay
  (traces)   (session recording)
```

### Terminal Runtime

```
  POST /api/terminal/execute
         |
         v
  +--------------------+     +-------------------------+
  | GovernanceValidator |---->| ExecutionGovernance     |
  +--------------------+     | (command validation)    |
         |                   +-------------------------+
         v
  +--------------------+
  | TerminalRuntime    |
  | - Session Store    |
  | - Command Executor |
  | - Output Capture   |
  +--------------------+
         |
    +----+----+
    |         |
    v         v
  Telemetry  Replay
  (traces)   (session recording)
```

### Workflow Engine

```
  POST /api/workflow/execute
         |
         v
  +--------------------+     +-------------------------+
  | GovernanceValidator |---->| ExecutionGovernance     |
  +--------------------+     | (step type validation)  |
         |                   +-------------------------+
         v
  +--------------------+
  | WorkflowEngine     |
  | - Definition Store |
  | - Step Resolver    |
  | - Execution Mgr   |
  +--------------------+
         |
         v
  +--------------------+
  | Step Execution     |
  | (sequential, with  |
  |  dependency order) |
  +--------------------+
         |
    +----+----+
    |         |
    v         v
  Telemetry  Replay
  (per-step) (execution recording)
```

### Skill Runtime

```
  POST /api/skills/invoke
         |
         v
  +--------------------+     +-------------------------+
  | GovernanceValidator |---->| ExecutionGovernance     |
  +--------------------+     | (skill ID validation)   |
         |                   +-------------------------+
         v
  +--------------------+
  | SkillRuntime       |
  | - Skill Registry   |
  | - Invocation Exec  |
  | - Result Capture   |
  +--------------------+
         |
    +----+----+
    |         |
    v         v
  Telemetry  Replay
  (traces)   (invocation recording)
```

---

## Integration Layer

### ExecutionGovernanceValidator

Bridges the GovernanceEngine with execution runtimes:

```
  +----------------------------+
  | ExecutionGovernanceValidator|
  +----------------------------+
         |
         v
  +------------------+
  | GovernanceEngine |
  +------------------+
```

- Validates browser URLs against allowed patterns
- Validates terminal commands against permitted commands
- Validates workflow step types
- Validates skill IDs against registered skills

### ExecutionTelemetryCollector

Bridges the TelemetryCollector with execution runtimes:

- Records browser action traces
- Records terminal command traces
- Records workflow step traces
- Records skill invocation traces

### ExecutionReplayManager

Bridges the ReplayRecorder with execution runtimes:

- Records browser session replay data
- Records terminal session replay data
- Records workflow execution replay data
- Provides replay retrieval by session type and ID

---

## Request Lifecycle

Every API request follows this lifecycle:

```
  1. HTTP Request arrives
         |
         v
  2. FastAPI route handler invoked
         |
         v
  3. Governance validation
         |
    +----+----+
    |         |
   PASS     DENY --> 403 + Audit log
    |
    v
  4. Operation execution (via runtime)
         |
         v
  5. Event dispatched (EventBus)
         |
         v
  6. Telemetry recorded (TelemetryCollector)
         |
         v
  7. Replay data recorded (ReplayRecorder)
         |
         v
  8. HTTP Response returned
```

---

## Dependency Injection

All components are wired via the `create_app()` factory in `backend/main.py`:

```
create_app()
  |
  +-- RuntimeExecutionContext()
  |
  +-- RuntimeManager(context)
  +-- EventBus(context)
  +-- GovernanceEngine(context)
  +-- AuditLogger(context)
  +-- TelemetryCollector(context)
  +-- RuntimeHealthMonitor(context)
  +-- ReplayRecorder(context)
  |
  +-- BrowserRuntime(context)
  +-- TerminalRuntime(context)
  +-- WorkflowEngine(context)
  +-- SkillRuntime(context)
  |
  +-- ExecutionGovernanceValidator(context, governance_engine)
  +-- ExecutionTelemetryCollector(context, telemetry_collector)
  +-- ExecutionReplayManager(context, replay_recorder)
  |
  +-- create_router(context, runtime_manager, event_bus, ...)
  +-- create_execution_router(context, browser_runtime, ...)
```

This structure ensures:
- All state is explicit and inspectable
- No hidden dependencies or global state
- Components are independently testable
- The full system is configurable at the composition root

---

## Frontend Architecture

```
  +-------------------------------------------+
  |           Next.js App (Port 3000)          |
  +-------------------------------------------+
  |                                           |
  |  +----------+  +---------------+          |
  |  | Layout   |  | API Client    |--------->| Backend
  |  | (Dark)   |  | (lib/api.ts)  |  HTTP    | :8000
  |  +----------+  +---------------+          |
  |       |                                   |
  |       v                                   |
  |  +-------------------------------------------+
  |  |            Components                      |
  |  | - RuntimeHealth    - WorkflowView          |
  |  | - GovernanceStatus - ExecutionTelemetry    |
  |  | - ReplayInspection                         |
  |  +-------------------------------------------+
  |                                           |
  +-------------------------------------------+
```

- Dark theme (#0d1117 background, #161b22 panels, #30363d borders)
- Client components with `'use client'` directive
- React hooks (useState, useEffect) for state and data fetching
- Next.js rewrites proxy `/api/*` to the backend
