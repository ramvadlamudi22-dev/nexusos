# Multi-Agent Runtime

**Module:** `nexusos.agents`  
**Status:** Architecture Specification  
**Principle:** Specialized governed agents with deterministic coordination

---

## Overview

The Multi-Agent Runtime provides a framework for specialized agents that collaborate through governed communication channels. Each agent has a defined role, capability boundary, and communication protocol. All inter-agent coordination is deterministic, observable, and replayable.

---

## Agent Architecture

```
┌─────────────────────────────────────────────────────────┐
│                       Agent                               │
├─────────────────────────────────────────────────────────┤
│  id: string                                              │
│  role: AgentRole                                         │
│  state: IDLE | PLANNING | EXECUTING | WAITING | ERROR    │
│  capabilities: Capability[]                              │
│  inbox: Message[]                                        │
│  outbox: Message[]                                       │
│  memory: AgentMemory                                     │
│  governance_scope: PolicyScope                           │
│  execution_context: RuntimeExecutionContext               │
└─────────────────────────────────────────────────────────┘
```

---

## Agent Roles

### Planner Agent
```
Role: Decomposes high-level objectives into execution graphs
Capabilities: graph_create, graph_validate, dependency_resolve
Inputs: Objective description, constraints, available resources
Outputs: ExecutionGraph definition
Governance: Cannot execute — only plans
```

### Executor Agent
```
Role: Executes individual nodes within an execution graph
Capabilities: browser_action, terminal_command, skill_invoke
Inputs: Node definition, inputs, execution context
Outputs: Node results, artifacts
Governance: Validated per-operation by governance layer
```

### Governance Agent
```
Role: Evaluates policy compliance for all operations
Capabilities: policy_evaluate, audit_record, decision_cache
Inputs: Action requests from other agents
Outputs: Permit/deny decisions with audit records
Governance: Self-governing (Zone 0 trust)
```

### Telemetry Agent
```
Role: Collects, aggregates, and reports operational metrics
Capabilities: metric_record, trace_start, health_evaluate
Inputs: Operation events from all agents
Outputs: Metrics, traces, health assessments
Governance: Read-only observation (cannot modify state)
```

### Replay Agent
```
Role: Records operations and manages replay sessions
Capabilities: record_operation, replay_session, verify_replay
Inputs: All operation records from other agents
Outputs: Replay sessions, verification reports
Governance: Append-only recording (cannot delete)
```

### Artifact Agent
```
Role: Manages artifact lifecycle, indexing, and lineage
Capabilities: artifact_store, artifact_index, lineage_track
Inputs: Artifacts produced by executor agent
Outputs: Indexed artifacts with metadata and lineage
Governance: Retention policies enforced
```

### Recovery Agent
```
Role: Detects failures and orchestrates recovery
Capabilities: health_monitor, diagnose, recover, restart
Inputs: Health state changes, failure events
Outputs: Recovery actions, diagnostic reports
Governance: Recovery actions validated before execution
```

---

## Communication Graph

```
                    ┌──────────────┐
                    │   Planner    │
                    │    Agent     │
                    └──────┬───────┘
                           │ execution_graph
                           ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Governance  │◄───│   Executor   │───→│  Telemetry   │
│    Agent     │    │    Agent     │    │    Agent     │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                    │
       │ audit             │ artifacts          │ metrics
       ▼                   ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Replay     │    │  Artifact    │    │  Recovery    │
│    Agent     │    │    Agent     │    │    Agent     │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## Message Protocol

```
┌─────────────────────────────────────────────────────────┐
│                      Message                             │
├─────────────────────────────────────────────────────────┤
│  id: string (deterministic)                              │
│  from: AgentId                                           │
│  to: AgentId                                             │
│  type: REQUEST | RESPONSE | EVENT | COMMAND              │
│  action: string                                          │
│  payload: Record<string, unknown>                        │
│  correlation_id: string (links request/response)         │
│  timestamp: ISO string                                   │
│  sequence: number (monotonic per sender)                 │
│  governance_decision_id: string (if validated)           │
└─────────────────────────────────────────────────────────┘
```

### Communication Rules

1. All messages pass through the governance agent for validation
2. Messages are ordered by sequence number (deterministic)
3. All messages are recorded by the replay agent
4. Agents cannot communicate outside their declared channels
5. Message delivery is guaranteed (at-least-once with idempotency)

---

## Shared Runtime Memory

```
┌─────────────────────────────────────────────────────────┐
│                  SharedMemory                             │
├─────────────────────────────────────────────────────────┤
│  execution_state: Map<string, ExecutionState>            │
│  artifact_index: ArtifactIndex                           │
│  health_graph: HealthGraph                               │
│  event_log: Event[] (append-only)                        │
│  governance_decisions: Decision[] (append-only)          │
│                                                         │
│  Access: Read by all agents                              │
│  Write: Only by owning agent (enforced)                  │
│  Observe: All writes emit events                         │
└─────────────────────────────────────────────────────────┘
```

---

## Orchestration Patterns

### Sequential Delegation
```
Planner → Executor(step1) → Executor(step2) → Executor(step3)
```

### Parallel Fan-Out
```
Planner → [Executor(A), Executor(B), Executor(C)] → Join
```

### Governance Gate
```
Executor → Governance(validate) → [permitted] → Executor(continue)
                                → [denied] → Recovery(handle)
```

### Recovery Loop
```
Executor(fail) → Recovery(diagnose) → Recovery(fix) → Executor(retry)
```

---

## Deterministic Coordination

All agent coordination is deterministic:
- Message ordering is by sequence number (not wall-clock time)
- Agent state transitions are explicit and inspectable
- Shared memory writes are serialized
- Parallel execution uses deterministic scheduling (round-robin by agent ID)
- Random decisions use seeded PRNG recorded for replay

---

## Integration with Existing Code

| Architecture Component | Current Implementation |
|----------------------|----------------------|
| Executor capabilities | `BrowserRuntime`, `TerminalRuntime`, `SkillRuntime` |
| Governance validation | `GovernanceEngine.validate_action()` |
| Telemetry collection | `TelemetryCollector`, `ExecutionTelemetryCollector` |
| Replay recording | `ReplayRecorder`, `ExecutionReplayManager` |
| Artifact storage | In-memory (to be extended) |
| Health monitoring | `RuntimeHealthMonitor` |
| Event bus | `EventBus` (pub/sub with sequences) |
| Workflow planning | `WorkflowEngine` (graph creation + execution) |

Evolution extends with: explicit agent boundaries, message protocol, shared memory, governed communication channels, and deterministic coordination.
