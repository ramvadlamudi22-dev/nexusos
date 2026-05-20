# Multi-Agent Runtime

**Module:** `nexusos.runtime.agents`  
**Version:** 2.0  
**Principle:** Specialized agents with governed coordination and deterministic orchestration

---

## Design Intent

The Multi-Agent Runtime decomposes NexusOS operations into specialized agents that collaborate through governed message channels. Each agent has a single responsibility, declared capabilities, and bounded autonomy. All inter-agent communication is deterministic, observable, and replayable.

---

## Agent Model

```typescript
interface Agent {
  id: string;
  role: AgentRole;
  state: AgentState;
  zone: TrustZone;                   // Governance zone
  capabilities: string[];            // Declared operations
  inbox: MessageQueue;
  outbox: MessageQueue;
  memory: AgentMemory;
  execution_context: RuntimeExecutionContext;
  
  // Lifecycle
  initialize(): Promise<void>;
  process(message: Message): Promise<Message | null>;
  shutdown(): Promise<void>;
}

enum AgentState {
  INITIALIZING = "INITIALIZING",
  IDLE         = "IDLE",
  PROCESSING   = "PROCESSING",
  WAITING      = "WAITING",
  ERROR        = "ERROR",
  SHUTDOWN     = "SHUTDOWN",
}

enum AgentRole {
  PLANNER     = "PLANNER",
  EXECUTOR    = "EXECUTOR",
  GOVERNANCE  = "GOVERNANCE",
  TELEMETRY   = "TELEMETRY",
  REPLAY      = "REPLAY",
  ARTIFACT    = "ARTIFACT",
  RECOVERY    = "RECOVERY",
}
```

---

## Agent Specifications

### Planner Agent

```
Role: Decomposes objectives into execution graphs
Zone: 1 (ORCHESTRATION)
Capabilities: graph.create, graph.validate, graph.optimize
Input: Objective + constraints + available resources
Output: ExecutionGraph definition
Constraints:
  - Cannot execute operations directly
  - Cannot modify governance policies
  - Must validate graphs before submission
  - Maximum graph complexity: 100 nodes
```

### Executor Agent

```
Role: Executes individual operations within graphs
Zone: 2 (EXECUTION)
Capabilities: browser.*, terminal.*, skill.*
Input: Node definition + inputs + context
Output: Node results + artifacts
Constraints:
  - Every operation validated by governance agent
  - Sandboxed per-session
  - Timeout-enforced
  - Cannot access other sessions
```

### Governance Agent

```
Role: Evaluates all operations against policies
Zone: 0 (KERNEL)
Capabilities: policy.evaluate, audit.record, decision.cache
Input: Action requests from all agents
Output: Permit/deny decisions
Constraints:
  - Self-governing (highest trust)
  - Cannot be overridden by other agents
  - Must audit every decision
  - Must respond within 100ms
```

### Telemetry Agent

```
Role: Observes and records all operations
Zone: 1 (ORCHESTRATION)
Capabilities: metric.record, trace.manage, event.emit
Input: Operation events from all agents
Output: Metrics, traces, health assessments
Constraints:
  - Read-only observation (cannot modify state)
  - Cannot block operations
  - Must not introduce latency >5ms
```

### Replay Agent

```
Role: Records operations and manages replay
Zone: 1 (ORCHESTRATION)
Capabilities: record.operation, replay.session, verify.replay
Input: All operation records
Output: Replay sessions, verification reports
Constraints:
  - Append-only recording (cannot delete)
  - Cannot modify recorded data
  - Must record before operation completes
```

### Artifact Agent

```
Role: Manages artifact lifecycle
Zone: 1 (ORCHESTRATION)
Capabilities: artifact.store, artifact.index, lineage.track
Input: Artifacts from executor agent
Output: Indexed artifacts with metadata
Constraints:
  - Content-addressed storage (immutable)
  - Retention policies enforced
  - Cannot modify stored artifacts
```

### Recovery Agent

```
Role: Detects and recovers from failures
Zone: 1 (ORCHESTRATION)
Capabilities: health.monitor, diagnose, recover.execute
Input: Health state changes, failure events
Output: Recovery actions, diagnostic reports
Constraints:
  - Recovery actions validated by governance
  - Cannot escalate beyond declared level
  - Must record all recovery attempts
```

---

## Communication Architecture

### Message Protocol

```typescript
interface Message {
  id: string;                        // Deterministic (SHA-256)
  type: MessageType;
  from: string;                      // Agent ID
  to: string;                        // Agent ID or broadcast channel
  correlation_id: string;            // Links request/response pairs
  timestamp: string;
  sequence: number;                  // Monotonic per sender
  payload: Record<string, unknown>;
  governance_decision_id: string | null;
  ttl_ms: number;                    // Message expiration
}

enum MessageType {
  REQUEST    = "REQUEST",     // Expects response
  RESPONSE   = "RESPONSE",   // Reply to request
  EVENT      = "EVENT",       // Notification (no response expected)
  COMMAND    = "COMMAND",     // Directive (must be executed)
}
```

### Communication Rules

1. **Governance mediation:** All messages between agents pass through the governance agent for validation (except governance agent's own responses)
2. **Deterministic ordering:** Messages processed in sequence number order
3. **Replay recording:** All messages recorded by replay agent
4. **Channel isolation:** Agents can only communicate on declared channels
5. **Delivery guarantee:** At-least-once with idempotency keys
6. **Timeout enforcement:** Unacknowledged messages expire after TTL

---

## Orchestration Topology

```
                         ┌─────────────────┐
                         │  Planner Agent  │
                         │                 │
                         │  Objectives →   │
                         │  Execution      │
                         │  Graphs         │
                         └────────┬────────┘
                                  │ graph.submit
                                  ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│ Governance Agent│◄─────│ Executor Agent  │─────→│ Telemetry Agent │
│                 │      │                 │      │                 │
│ validate.*      │      │ execute.*       │      │ observe.*       │
│ audit.*         │      │ browser.*       │      │ metric.*        │
│ decide.*        │      │ terminal.*      │      │ trace.*         │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                         │
         │ audit                  │ artifacts               │ health
         ▼                        ▼                         ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Replay Agent   │      │ Artifact Agent  │      │ Recovery Agent  │
│                 │      │                 │      │                 │
│ record.*        │      │ store.*         │      │ detect.*        │
│ replay.*        │      │ index.*         │      │ recover.*       │
│ verify.*        │      │ lineage.*       │      │ diagnose.*      │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

---

## Shared Runtime Memory

```typescript
interface SharedMemory {
  // Execution state (owned by Executor Agent)
  executions: Map<string, ExecutionState>;
  
  // Artifact index (owned by Artifact Agent)
  artifacts: ArtifactIndex;
  
  // Health graph (owned by Recovery Agent)
  health: HealthGraph;
  
  // Event log (owned by Telemetry Agent, append-only)
  events: RuntimeEvent[];
  
  // Governance decisions (owned by Governance Agent, append-only)
  decisions: Decision[];
  
  // Access control
  read(key: string, requester: AgentId): unknown;
  write(key: string, value: unknown, owner: AgentId): void;
}
```

### Memory Access Rules

| Agent | Read | Write |
|-------|------|-------|
| Planner | executions, health | — |
| Executor | executions (own) | executions (own) |
| Governance | all | decisions |
| Telemetry | all | events |
| Replay | all | — (records externally) |
| Artifact | artifacts | artifacts |
| Recovery | health, executions | health |

---

## Deterministic Coordination

All coordination is deterministic:

1. **Message ordering:** Sequence numbers, not wall-clock time
2. **Scheduling:** Round-robin by agent ID for equal-priority messages
3. **Parallel execution:** Deterministic fork-join with ordered results
4. **Conflict resolution:** Higher-zone agent wins ties
5. **Random decisions:** Seeded PRNG, seed recorded for replay

---

## Agent Lifecycle

```
CREATE → INITIALIZE → IDLE ←→ PROCESSING → SHUTDOWN
                        │                      ↑
                        └── ERROR ─────────────┘
                              │
                              └── (Recovery Agent handles)
```

---

## Mapping to Current Implementation

| New Concept | Existing Code | Gap |
|-------------|--------------|-----|
| Executor capabilities | `BrowserRuntime`, `TerminalRuntime`, `SkillRuntime` | Wrap as agent |
| Governance validation | `GovernanceEngine` | Wrap as agent |
| Telemetry collection | `TelemetryCollector`, `ExecutionTelemetryCollector` | Wrap as agent |
| Replay recording | `ReplayRecorder` | Wrap as agent |
| Health monitoring | `RuntimeHealthMonitor` | Wrap as recovery agent |
| Event bus | `EventBus` | Extend as message transport |
| Workflow planning | `WorkflowEngine` | Wrap as planner agent |
| Shared state | In-memory dicts in main.py | Formalize as SharedMemory |
