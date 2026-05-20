# Execution Graph Engine

**Module:** `nexusos.execution_graph`  
**Status:** Architecture Specification  
**Principle:** Deterministic DAG-based workflow orchestration

---

## Overview

The Execution Graph Engine is the core orchestration primitive of NexusOS. Every workflow is represented as a directed acyclic graph (DAG) where nodes are execution units and edges are dependency constraints. The engine guarantees deterministic execution order, supports checkpointing, rollback, and idempotent replay.

---

## Graph Model

### Node Types

```
┌─────────────────────────────────────────────────────────┐
│                    ExecutionNode                          │
├─────────────────────────────────────────────────────────┤
│  id: string (SHA-256 deterministic)                      │
│  type: COMPUTE | IO | GOVERNANCE | CHECKPOINT | BRANCH   │
│  state: PENDING | READY | RUNNING | COMPLETED | FAILED   │
│  inputs: Record<string, Artifact>                        │
│  outputs: Record<string, Artifact>                       │
│  config: NodeConfig                                      │
│  retry_policy: RetryPolicy                               │
│  timeout_ms: number                                      │
│  idempotency_key: string                                 │
└─────────────────────────────────────────────────────────┘
```

### Edge Types

```
┌─────────────────────────────────────────────────────────┐
│                    DependencyEdge                         │
├─────────────────────────────────────────────────────────┤
│  source_id: string                                       │
│  target_id: string                                       │
│  type: DATA | CONTROL | GOVERNANCE | CHECKPOINT          │
│  condition: EdgeCondition (optional)                     │
│  artifact_mapping: Record<string, string>                │
└─────────────────────────────────────────────────────────┘
```

### Graph Definition

```
┌─────────────────────────────────────────────────────────┐
│                  ExecutionGraph                           │
├─────────────────────────────────────────────────────────┤
│  id: string                                              │
│  version: string                                         │
│  nodes: ExecutionNode[]                                  │
│  edges: DependencyEdge[]                                 │
│  checkpoints: CheckpointPolicy[]                         │
│  governance_gates: GovernanceGate[]                       │
│  metadata: GraphMetadata                                 │
└─────────────────────────────────────────────────────────┘
```

---

## Execution State Machine

```
                    ┌──────────┐
                    │ PENDING  │
                    └────┬─────┘
                         │ all dependencies satisfied
                         ▼
                    ┌──────────┐
                    │  READY   │
                    └────┬─────┘
                         │ scheduler picks up
                         ▼
                    ┌──────────┐
              ┌─────│ RUNNING  │─────┐
              │     └──────────┘     │
              │ success              │ failure
              ▼                      ▼
        ┌──────────┐          ┌──────────┐
        │COMPLETED │          │  FAILED  │
        └──────────┘          └────┬─────┘
                                   │ retry policy
                                   ▼
                              ┌──────────┐
                              │ RETRYING │──→ READY
                              └──────────┘
                                   │ max retries exceeded
                                   ▼
                              ┌──────────┐
                              │ ABORTED  │
                              └──────────┘
```

---

## Topological Execution

The engine resolves execution order using Kahn's algorithm (topological sort):

1. Compute in-degree for all nodes
2. Enqueue all nodes with in-degree 0 (no dependencies)
3. For each dequeued node:
   - Execute the node
   - Decrement in-degree of all dependents
   - Enqueue dependents with in-degree 0
4. Parallel execution of independent nodes at same depth level

### Cycle Detection

Cycles are detected at graph registration time. A graph with cycles is rejected — it cannot be executed deterministically.

---

## Checkpoint System

```
┌─────────────────────────────────────────────────────────┐
│                  CheckpointPolicy                         │
├─────────────────────────────────────────────────────────┤
│  trigger: AFTER_NODE | AFTER_LEVEL | PERIODIC | MANUAL   │
│  storage: CheckpointStorage                              │
│  retention: Duration                                     │
│  includes: [node_outputs, graph_state, telemetry]        │
└─────────────────────────────────────────────────────────┘
```

Checkpoints capture:
- All completed node outputs
- Current graph execution state
- Pending node queue
- Telemetry accumulated to that point

### Rollback

Rollback restores execution to a checkpoint:
1. Load checkpoint state
2. Reset all nodes after checkpoint to PENDING
3. Clear outputs produced after checkpoint
4. Resume execution from checkpoint position

---

## Retry Policies

```
┌─────────────────────────────────────────────────────────┐
│                    RetryPolicy                            │
├─────────────────────────────────────────────────────────┤
│  max_attempts: number                                    │
│  backoff: FIXED | EXPONENTIAL | LINEAR                   │
│  base_delay_ms: number                                   │
│  max_delay_ms: number                                    │
│  retryable_errors: string[] (error type whitelist)       │
│  idempotent: boolean                                     │
└─────────────────────────────────────────────────────────┘
```

Only idempotent nodes may be retried. Non-idempotent nodes that fail transition directly to ABORTED.

---

## Branch Recovery

When a node fails and cannot be retried:
1. Mark the node ABORTED
2. Propagate ABORTED to all transitive dependents
3. Execute any registered recovery branches
4. Recovery branches are alternative subgraphs attached to failure edges

```
    [Node A] ──success──→ [Node B]
        │
        └──failure──→ [Recovery Node R] ──→ [Node B alternate input]
```

---

## Execution Manifest Format

```json
{
  "manifest_version": "1.0.0",
  "graph_id": "wf-abc123",
  "execution_id": "exec-def456",
  "start_timestamp": "2026-05-19T18:00:00Z",
  "end_timestamp": "2026-05-19T18:00:05Z",
  "state": "COMPLETED",
  "nodes_executed": 4,
  "nodes_failed": 0,
  "checkpoints": ["cp-001", "cp-002"],
  "artifacts_produced": ["art-001", "art-002", "art-003"],
  "governance_decisions": ["gov-001"],
  "telemetry_summary": {
    "total_duration_ms": 5000,
    "node_durations": {"init": 100, "validate": 200, "execute": 4500, "aggregate": 200}
  }
}
```

---

## Graph Serialization

Graphs are serialized as JSON with deterministic key ordering (sorted keys) to ensure identical serialization produces identical checksums.

```
graph_checksum = SHA-256(canonical_json(graph_definition))
```

This enables:
- Graph version comparison
- Replay verification (same graph → same execution)
- Tamper detection on stored graph definitions

---

## Integration Points

| System | Integration |
|--------|-------------|
| Governance | GovernanceGate nodes require policy approval before execution proceeds |
| Replay | All node inputs/outputs recorded for deterministic replay |
| Telemetry | Execution metrics emitted per node (duration, status, retries) |
| Artifacts | Node outputs stored as typed artifacts with lineage |
| Self-Healing | Failed nodes trigger recovery orchestration |

---

## Implementation Mapping to Existing Code

| Architecture Component | Current Implementation |
|----------------------|----------------------|
| ExecutionGraph | `WorkflowDefinition` (backend/workflow/models.py) |
| ExecutionNode | `WorkflowStep` |
| DependencyEdge | `WorkflowStep.depends_on` |
| Topological Sort | `WorkflowEngine._resolve_execution_order()` |
| State Machine | `WorkflowExecutionState` enum |
| Execution Record | `WorkflowExecution` |
| Step Result | `WorkflowStepResult` |

The existing `WorkflowEngine` implements the core of this architecture. Evolution extends it with checkpoints, retry policies, branch recovery, and governance gates.
