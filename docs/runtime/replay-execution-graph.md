# Replayable Execution Graph

**Module:** `nexusos.runtime.replay_graph`  
**Principle:** Every execution is a graph. Every graph is replayable. Divergence is a defect.

---

## Execution Graph as Replay Unit

The execution graph is both the orchestration model AND the replay unit. A completed execution graph contains everything needed to reconstruct the exact execution:

```typescript
interface ReplayableExecutionGraph {
  // Graph definition (what to execute)
  definition: {
    id: string;
    nodes: ExecutionNode[];
    edges: DependencyEdge[];
    checksum: string;
  };
  
  // Execution record (what happened)
  execution: {
    id: string;
    start_time: string;
    end_time: string;
    time_source: number[];         // All timestamps used
    node_results: NodeResult[];
    state_transitions: StateTransition[];
    governance_decisions: Decision[];
    recovery_actions: RemediationRecord[];
  };
  
  // Artifacts (what was produced)
  artifacts: {
    id: string;
    type: string;
    content_hash: string;
    node_id: string;
  }[];
  
  // Replay metadata
  replay: {
    replayable: boolean;
    replay_requirements: string[];  // What's needed to replay
    determinism_score: number;      // 0-1 (1 = fully deterministic)
    external_dependencies: string[]; // Things that might differ on replay
  };
}
```

---

## State Transitions

Every state change is recorded as a transition:

```typescript
interface StateTransition {
  sequence: number;                // Global ordering
  timestamp: string;
  node_id: string;
  from_state: NodeState;
  to_state: NodeState;
  trigger: string;                 // What caused the transition
  metadata: Record<string, unknown>;
}
```

### Transition Log Example

```
seq=1   T+0ms     graph      → EXECUTING     (trigger: api_call)
seq=2   T+1ms     node:init  → READY         (trigger: no_dependencies)
seq=3   T+2ms     node:init  → RUNNING       (trigger: scheduler)
seq=4   T+102ms   node:init  → COMPLETED     (trigger: success)
seq=5   T+103ms   node:gov   → READY         (trigger: dependency_met)
seq=6   T+103ms   node:exec  → READY         (trigger: dependency_met)
seq=7   T+104ms   node:gov   → RUNNING       (trigger: scheduler)
seq=8   T+104ms   node:exec  → RUNNING       (trigger: scheduler)
seq=9   T+110ms   governance → PERMITTED     (trigger: policy_eval)
seq=10  T+304ms   node:gov   → COMPLETED     (trigger: success)
seq=11  T+4604ms  node:exec  → COMPLETED     (trigger: success)
seq=12  T+4605ms  node:join  → READY         (trigger: all_deps_met)
seq=13  T+4606ms  node:join  → RUNNING       (trigger: scheduler)
seq=14  T+4806ms  node:join  → COMPLETED     (trigger: success)
seq=15  T+4807ms  graph      → COMPLETED     (trigger: all_nodes_done)
```

---

## Workflow Checkpoints

Checkpoints capture graph state at a point in time:

```typescript
interface GraphCheckpoint {
  id: string;
  execution_id: string;
  sequence_at_checkpoint: number;   // Transition sequence number
  timestamp: string;
  
  // State snapshot
  node_states: Record<string, NodeState>;
  completed_outputs: Record<string, ArtifactRef>;
  pending_queue: string[];          // Node IDs waiting to execute
  
  // Context
  time_source_position: number;     // Index into recorded timestamps
  telemetry_snapshot: TelemetryState;
  governance_state: GovernanceState;
  
  // Integrity
  checksum: string;                 // SHA-256 of checkpoint content
}
```

### Checkpoint Triggers

| Trigger | When | Purpose |
|---------|------|---------|
| NODE_COMPLETE | After each node completes | Fine-grained rollback |
| LEVEL_COMPLETE | After all nodes at a depth level | Batch rollback |
| GOVERNANCE_GATE | Before governance-gated node | Pre-decision snapshot |
| EXPLICIT | Node configured with `checkpoint_after: true` | Critical points |
| PERIODIC | Every N seconds of execution | Time-based safety net |

---

## Replay Manifests

A replay manifest is the complete recipe to reproduce an execution:

```typescript
interface ReplayManifest {
  manifest_version: "1.0.0";
  execution_id: string;
  graph_checksum: string;
  
  // Inputs needed for replay
  inputs: {
    graph_definition: ExecutionGraph;
    initial_state: Record<string, unknown>;
    time_source: number[];           // Recorded timestamps
    environment: EnvironmentSnapshot;
    governance_policies: Policy[];
  };
  
  // Expected outputs (for verification)
  expected_outputs: {
    final_state: GraphState;
    node_results: Record<string, NodeResult>;
    artifacts: ArtifactRef[];
    governance_decisions: Decision[];
  };
  
  // Verification
  verification: {
    determinism_score: number;
    external_dependencies: ExternalDep[];
    replay_warnings: string[];
  };
}
```

---

## Artifact Lineage

Every artifact traces back to its producing node:

```
ExecutionGraph: "deployment-verify"
    │
    ├── Node: "check-homepage"
    │   ├── Artifact: screenshot-homepage.png (hash: ab3f...)
    │   └── Artifact: page-result-homepage.json (hash: cd91...)
    │
    ├── Node: "check-dashboard"
    │   ├── Artifact: screenshot-dashboard.png (hash: ef45...)
    │   └── Artifact: page-result-dashboard.json (hash: 12bc...)
    │
    ├── Node: "record-video"
    │   └── Artifact: walkthrough.webm (hash: 34de...)
    │
    └── Node: "generate-report"
        ├── Artifact: verification-report.json (hash: 56fg...)
        └── Artifact: proof-manifest.json (hash: 78hi...)
```

Each artifact knows:
- Which execution produced it
- Which node produced it
- What inputs the node received
- What other artifacts were produced alongside it
- Its content hash for integrity verification

---

## Deterministic Replay Validation

Replay verification compares original execution to replay:

```typescript
interface ReplayVerification {
  original_execution_id: string;
  replay_execution_id: string;
  
  // Comparison results
  state_transitions_match: boolean;
  node_results_match: boolean;
  artifacts_match: boolean;         // Content hashes identical
  governance_decisions_match: boolean;
  
  // Divergences (if any)
  divergences: {
    sequence: number;
    type: "STATE" | "OUTPUT" | "TIMING" | "GOVERNANCE";
    expected: unknown;
    actual: unknown;
    probable_cause: string;
  }[];
  
  // Verdict
  verdict: "IDENTICAL" | "EQUIVALENT" | "DIVERGED";
  determinism_confirmed: boolean;
}
```

### Equivalence vs. Identity

- **IDENTICAL:** Byte-for-byte same outputs (fully deterministic)
- **EQUIVALENT:** Same logical results, minor timing differences (acceptable)
- **DIVERGED:** Different results (system defect or external change)

---

## Failure Replay Analysis

When a failure occurs, replay the execution to understand why:

```
1. Load execution graph + replay manifest
2. Replay up to the failure point
3. At failure point:
   a. Inspect all inputs to the failing node
   b. Compare environment state to original
   c. Check if external dependencies changed
   d. Identify root cause
4. Generate failure analysis report
```

This enables post-mortem debugging without reproducing the failure in production.

---

## Mapping to Current Implementation

| Concept | Existing | Gap |
|---------|----------|-----|
| Graph definition | `WorkflowDefinition` | Add checksum, ports |
| Node execution | `WorkflowEngine.execute_workflow()` | Add state transition recording |
| Topological sort | `_resolve_execution_order()` | ✓ Already implemented |
| Execution record | `WorkflowExecution` | Add time_source, transitions |
| Replay recording | `ReplayRecorder` | Add manifest generation |
| Time injection | `RuntimeExecutionContext(time_source=)` | ✓ Already supports |
| Artifact tracking | In-memory lists | Add lineage, content hashing |
| Checkpoints | Not implemented | New: state snapshot system |
| Replay verification | Not implemented | New: comparison engine |
