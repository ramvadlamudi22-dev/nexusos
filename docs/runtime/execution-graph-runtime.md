# Execution Graph Runtime

**Module:** `nexusos.runtime.execution_graph`  
**Version:** 2.0  
**Principle:** All orchestration flows through deterministic execution graphs

---

## Design Intent

The Execution Graph Runtime replaces linear workflow scripts with a DAG-based execution model. Every operation — browser action, terminal command, governance check, telemetry emission — is a node in a directed acyclic graph. The runtime resolves dependencies, manages state transitions, enforces governance at each node, and produces replayable execution records.

---

## Core Schema

### ExecutionGraph

```typescript
interface ExecutionGraph {
  id: string;                          // SHA-256(name + version + created_at)
  name: string;
  version: string;                     // Semantic version
  created_at: string;                  // ISO timestamp
  checksum: string;                    // SHA-256 of canonical serialization
  nodes: ExecutionNode[];
  edges: DependencyEdge[];
  governance_gates: GovernanceGate[];
  checkpoint_policy: CheckpointPolicy;
  retry_defaults: RetryPolicy;
  metadata: Record<string, string>;
}
```

### ExecutionNode

```typescript
interface ExecutionNode {
  id: string;                          // Unique within graph
  type: NodeType;
  name: string;
  config: NodeConfig;
  inputs: PortDefinition[];            // Declared input ports
  outputs: PortDefinition[];           // Declared output ports
  retry_policy: RetryPolicy | null;    // Override graph default
  timeout_ms: number;
  idempotent: boolean;                 // Safe to retry?
  governance_action: string;           // Action name for governance check
  checkpoint_after: boolean;           // Create checkpoint after completion
}

enum NodeType {
  COMPUTE    = "COMPUTE",     // Pure computation, no side effects
  BROWSER    = "BROWSER",     // Browser automation action
  TERMINAL   = "TERMINAL",    // Shell command execution
  GOVERNANCE = "GOVERNANCE",  // Policy evaluation gate
  CHECKPOINT = "CHECKPOINT",  // Explicit state snapshot
  BRANCH     = "BRANCH",      // Conditional routing
  JOIN       = "JOIN",        // Parallel convergence point
  SKILL      = "SKILL",       // Plugin invocation
  EMIT       = "EMIT",        // Telemetry/event emission
}
```

### DependencyEdge

```typescript
interface DependencyEdge {
  id: string;
  source_node: string;
  source_port: string;                 // Output port name
  target_node: string;
  target_port: string;                 // Input port name
  type: EdgeType;
  condition: EdgeCondition | null;     // For conditional edges
}

enum EdgeType {
  DATA       = "DATA",        // Artifact flows from source to target
  CONTROL    = "CONTROL",     // Execution ordering only
  FAILURE    = "FAILURE",     // Activated on source failure
  RECOVERY   = "RECOVERY",   // Recovery branch activation
}
```

---

## State Machine

```
┌───────────┐
│  PENDING  │ ← Initial state (dependencies not met)
└─────┬─────┘
      │ All input edges satisfied
      ▼
┌───────────┐
│   READY   │ ← Eligible for scheduling
└─────┬─────┘
      │ Governance gate passed + scheduler picks
      ▼
┌───────────┐
│  RUNNING  │ ← Actively executing
└─────┬─────┘
      │
      ├─── success ──→ ┌───────────┐
      │                │ COMPLETED │ ← Outputs available
      │                └───────────┘
      │
      ├─── failure ──→ ┌───────────┐
      │                │  FAILED   │
      │                └─────┬─────┘
      │                      │ retry_policy.max_attempts > 0
      │                      ▼
      │                ┌───────────┐
      │                │ RETRYING  │ ──→ READY (with backoff)
      │                └─────┬─────┘
      │                      │ retries exhausted
      │                      ▼
      │                ┌───────────┐
      │                │  ABORTED  │ ← Terminal failure
      │                └───────────┘
      │
      └─── timeout ──→ FAILED (timeout error)
```

### Graph-Level States

```
REGISTERED → VALIDATING → READY → EXECUTING → COMPLETED
                                      │
                                      ├──→ FAILED (unrecoverable)
                                      └──→ ROLLED_BACK (checkpoint restore)
```

---

## Execution Algorithm

```python
def execute_graph(graph: ExecutionGraph) -> ExecutionResult:
    # 1. Validate graph structure (no cycles, valid edges)
    validate_dag(graph)
    
    # 2. Initialize all nodes to PENDING
    node_states = {n.id: PENDING for n in graph.nodes}
    
    # 3. Compute initial ready set (nodes with no incoming edges)
    ready_queue = [n for n in graph.nodes if in_degree(n) == 0]
    
    # 4. Execute until all nodes complete or graph fails
    while ready_queue or any_running(node_states):
        # Schedule ready nodes (respecting parallelism limits)
        for node in ready_queue:
            # Governance check before execution
            decision = governance.validate(node.governance_action)
            if not decision.permitted:
                abort_node(node, decision.reason)
                continue
            
            # Execute node
            node_states[node.id] = RUNNING
            result = execute_node(node)
            
            if result.success:
                node_states[node.id] = COMPLETED
                # Propagate outputs to dependent nodes
                propagate_outputs(node, result.outputs)
                # Check if dependents are now ready
                update_ready_queue(node, ready_queue)
                # Checkpoint if configured
                if node.checkpoint_after:
                    create_checkpoint(graph, node_states)
            else:
                handle_failure(node, result, node_states, ready_queue)
        
    return build_execution_result(graph, node_states)
```

---

## Retry Orchestration

```typescript
interface RetryPolicy {
  max_attempts: number;              // 0 = no retry
  backoff_strategy: "FIXED" | "EXPONENTIAL" | "LINEAR";
  base_delay_ms: number;
  max_delay_ms: number;
  jitter: boolean;                   // Add randomness to prevent thundering herd
  retryable_errors: string[];        // Error type whitelist (empty = all)
  requires_idempotent: boolean;      // Only retry if node is idempotent
}
```

Retry decision tree:
1. Is the node marked idempotent? If not → ABORTED
2. Is the error type in retryable_errors? If not → ABORTED
3. Are retries remaining? If not → ABORTED
4. Compute backoff delay
5. Transition to RETRYING → wait → transition to READY

---

## Rollback Checkpoints

```typescript
interface Checkpoint {
  id: string;
  graph_execution_id: string;
  created_at: string;
  trigger_node_id: string;           // Node that triggered checkpoint
  node_states: Record<string, NodeState>;
  completed_outputs: Record<string, Artifact>;
  pending_inputs: Record<string, PortValue>;
  telemetry_snapshot: TelemetryState;
  checksum: string;                  // Integrity verification
}
```

Rollback procedure:
1. Load checkpoint state
2. Reset all nodes after checkpoint to PENDING
3. Discard outputs produced after checkpoint
4. Clear telemetry accumulated after checkpoint
5. Resume execution from checkpoint position
6. Record rollback event in audit trail

---

## Branch Recovery

When a node fails and cannot be retried, FAILURE edges activate:

```
[Node A] ──DATA──→ [Node B] ──DATA──→ [Node C]
    │
    └──FAILURE──→ [Recovery R] ──DATA──→ [Node C]
```

Recovery nodes receive:
- The failed node's inputs (for retry with different strategy)
- The failure context (error type, message, stack)
- The graph state at failure time

---

## Execution Lineage

Every execution produces a lineage record:

```typescript
interface ExecutionLineage {
  execution_id: string;
  graph_id: string;
  graph_version: string;
  parent_execution_id: string | null;  // If triggered by another execution
  trigger: "API" | "SCHEDULE" | "EVENT" | "RECOVERY";
  node_executions: NodeExecution[];
  total_duration_ms: number;
  artifacts_produced: string[];
  governance_decisions: string[];
  checkpoints_created: string[];
  final_state: GraphState;
}
```

---

## Orchestration Contracts

Each node type has a defined contract:

| Node Type | Inputs | Outputs | Side Effects |
|-----------|--------|---------|-------------|
| COMPUTE | Data artifacts | Data artifacts | None |
| BROWSER | URL, action config | Screenshots, DOM state | Browser state |
| TERMINAL | Command, env | stdout, stderr, exit_code | File system |
| GOVERNANCE | Action, resource | Decision | Audit record |
| CHECKPOINT | Graph state | Checkpoint ID | Storage |
| BRANCH | Condition value | Selected branch | None |
| JOIN | Multiple inputs | Merged output | None |
| SKILL | Invocation params | Skill result | Varies |
| EMIT | Metric/event data | Confirmation | Telemetry store |

---

## Mapping to Current Implementation

| New Concept | Existing Code | Gap |
|-------------|--------------|-----|
| ExecutionGraph | `WorkflowDefinition` | Add ports, checkpoints, governance gates |
| ExecutionNode | `WorkflowStep` | Add type enum, retry policy, idempotency |
| DependencyEdge | `depends_on` list | Add edge types, conditions, port mapping |
| State machine | `WorkflowExecutionState` | Add RETRYING, ABORTED, ROLLED_BACK |
| Topological sort | `_resolve_execution_order()` | Already implemented |
| Execution result | `WorkflowExecution` | Add lineage, checkpoints, artifacts |
| Governance gate | `ExecutionGovernanceValidator` | Integrate as node type |
| Retry | Not implemented | New: RetryPolicy per node |
| Checkpoint | Not implemented | New: state snapshot system |
| Branch recovery | Not implemented | New: FAILURE edge type |
