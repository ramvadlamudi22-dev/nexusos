# Replay Runtime

**Module:** `nexusos.runtime.replay`  
**Version:** 2.0  
**Principle:** Every execution is reconstructable. Divergence is a defect.

---

## Design Intent

The Replay Runtime enables deterministic reconstruction of any past execution. It captures all inputs, time sources, and environmental context needed to reproduce identical outputs. Replay is not debugging — it is verification. If replay diverges from the original, the system has a defect.

---

## Replay Session Model

```typescript
interface ReplaySession {
  id: string;
  source_execution_id: string;       // Original execution being replayed
  state: ReplayState;
  mode: ReplayMode;
  timeline: ReplayTimeline;
  time_source: RecordedTimestamps;
  position: TimelinePosition;
  verification: VerificationState;
  artifacts: ReplayArtifactSet;
}

enum ReplayState {
  LOADING    = "LOADING",
  READY      = "READY",
  PLAYING    = "PLAYING",
  PAUSED     = "PAUSED",
  COMPLETED  = "COMPLETED",
  DIVERGED   = "DIVERGED",
  ERROR      = "ERROR",
}

enum ReplayMode {
  FULL         = "FULL",          // Complete reconstruction
  PARTIAL      = "PARTIAL",       // From checkpoint to point
  STEPPED      = "STEPPED",       // One operation at a time
  DIFFERENTIAL = "DIFFERENTIAL",  // Compare two executions
  VERIFICATION = "VERIFICATION",  // Verify outputs match
}
```

---

## What Gets Recorded

### Browser Replay Records

```typescript
interface BrowserReplayRecord {
  session_id: string;
  sequence: number;
  timestamp: string;
  action: {
    type: BrowserActionType;
    target: string;
    value: string | null;
    options: Record<string, unknown>;
  };
  result: {
    success: boolean;
    error: string | null;
    screenshot_ref: string | null;
    dom_snapshot_ref: string | null;
  };
  page_state: {
    url: string;
    title: string;
    viewport: { width: number; height: number };
  };
  network_activity: NetworkEntry[];
}
```

### Workflow Replay Records

```typescript
interface WorkflowReplayRecord {
  execution_id: string;
  graph_definition: ExecutionGraph;  // Full graph for reconstruction
  node_executions: {
    node_id: string;
    sequence: number;
    state_transitions: { from: NodeState; to: NodeState; timestamp: string }[];
    inputs: Record<string, ArtifactRef>;
    outputs: Record<string, ArtifactRef>;
    duration_ms: number;
    governance_decision: Decision | null;
    retry_count: number;
  }[];
  checkpoints: Checkpoint[];
  final_state: GraphState;
}
```

### Terminal Replay Records

```typescript
interface TerminalReplayRecord {
  session_id: string;
  sequence: number;
  timestamp: string;
  command: string;
  working_dir: string;
  environment: Record<string, string>;
  result: {
    stdout: string;
    stderr: string;
    exit_code: number;
    duration_ms: number;
  };
}
```

---

## Timeline Reconstruction

The replay timeline merges all recorded operations into a single ordered sequence:

```typescript
interface ReplayTimeline {
  execution_id: string;
  total_duration_ms: number;
  entries: TimelineEntry[];
  
  // Navigation
  seek(position: number): void;
  step_forward(): TimelineEntry;
  step_backward(): TimelineEntry;
  
  // Filtering
  filter_by_component(component: string): TimelineEntry[];
  filter_by_time_range(start_ms: number, end_ms: number): TimelineEntry[];
}

interface TimelineEntry {
  sequence: number;                // Global ordering
  offset_ms: number;               // From execution start
  component: string;               // Which subsystem
  operation: string;               // What happened
  inputs: Record<string, unknown>; // Operation inputs
  outputs: Record<string, unknown>;// Operation outputs
  artifacts: string[];             // Produced artifact IDs
  governance: Decision | null;     // Associated decision
}
```

---

## Deterministic Playback

### Recorded Time Source

```python
class RecordedTimeSource:
    """Replays exact timestamps from original execution."""
    
    def __init__(self, recorded_timestamps: list[float]):
        self._timestamps = recorded_timestamps
        self._index = 0
    
    def __call__(self) -> float:
        if self._index >= len(self._timestamps):
            raise ReplayExhaustedError("No more recorded timestamps")
        ts = self._timestamps[self._index]
        self._index += 1
        return ts
    
    @property
    def position(self) -> int:
        return self._index
```

### Replay Execution

```python
def replay_execution(session: ReplaySession) -> ReplayResult:
    # 1. Create context with recorded time source
    context = RuntimeExecutionContext(time_source=session.time_source)
    
    # 2. Reconstruct all components with same initial state
    components = initialize_components(context)
    
    # 3. Replay each timeline entry in sequence
    for entry in session.timeline.entries:
        # Execute the operation with recorded inputs
        actual_output = execute_operation(entry, components)
        
        # Compare to recorded output
        if session.mode == ReplayMode.VERIFICATION:
            divergence = compare_outputs(entry.outputs, actual_output)
            if divergence:
                session.state = ReplayState.DIVERGED
                record_divergence(session, entry, divergence)
                if not session.continue_on_divergence:
                    return ReplayResult(verdict="DIVERGED", divergences=[divergence])
    
    return ReplayResult(verdict="MATCH", divergences=[])
```

---

## Screenshot Lineage

Every screenshot is linked to its execution context:

```typescript
interface ScreenshotLineage {
  screenshot_id: string;           // Content hash
  session_id: string;              // Browser session
  execution_id: string;            // Workflow execution
  node_id: string | null;          // Graph node that triggered it
  timeline_position: number;       // Position in replay timeline
  page_url: string;
  viewport: { width: number; height: number };
  captured_at: string;
  preceding_action: BrowserAction | null;
}
```

---

## Trace-Linked Execution

Every replay session links to its Playwright trace:

```typescript
interface TraceLink {
  replay_session_id: string;
  trace_file: string;              // Path to .zip trace
  trace_viewer_url: string;        // https://trace.playwright.dev compatible
  spans_count: number;
  screenshots_in_trace: number;
  network_entries: number;
  dom_snapshots: number;
}
```

---

## Replay Verification Report

```typescript
interface ReplayVerificationReport {
  session_id: string;
  source_execution_id: string;
  verdict: "MATCH" | "DIVERGED" | "PARTIAL_MATCH";
  total_operations: number;
  operations_verified: number;
  divergences: Divergence[];
  
  // Summary
  matching_percentage: number;
  first_divergence_at: number | null;  // Timeline position
  divergence_categories: Record<string, number>;
}

interface Divergence {
  timeline_position: number;
  operation: string;
  component: string;
  expected: unknown;
  actual: unknown;
  category: "OUTPUT_MISMATCH" | "STATE_MISMATCH" | "TIMING_DRIFT" |
            "MISSING_OPERATION" | "EXTRA_OPERATION" | "GOVERNANCE_CHANGE";
  severity: "CRITICAL" | "WARNING" | "INFO";
}
```

---

## Replay API

```
POST /api/replay/sessions                          → Create replay session
GET  /api/replay/sessions                          → List sessions
GET  /api/replay/sessions/{id}                     → Session details
POST /api/replay/sessions/{id}/start               → Begin replay
POST /api/replay/sessions/{id}/pause               → Pause
POST /api/replay/sessions/{id}/step                → Step forward
POST /api/replay/sessions/{id}/seek?position=N     → Seek to position
GET  /api/replay/sessions/{id}/timeline            → Full timeline
GET  /api/replay/sessions/{id}/timeline?from=A&to=B → Range
GET  /api/replay/sessions/{id}/verification        → Verification report
GET  /api/replay/sessions/{id}/divergences         → Divergence list
GET  /api/replay/sessions/{id}/artifacts           → Linked artifacts
POST /api/replay/sessions/{id}/compare/{other_id}  → Differential replay
```

---

## Mapping to Current Implementation

| New Concept | Existing Code | Gap |
|-------------|--------------|-----|
| Replay recording | `ReplayRecorder` | Add timeline sequencing |
| Browser recording | `BrowserSession.recording` | Add page state, network |
| Terminal recording | `TerminalSession.command_history` | Add environment capture |
| Workflow recording | `ExecutionReplayManager` | Add graph definition capture |
| Time injection | `RuntimeExecutionContext(time_source=)` | Already supports injection |
| Replay API | `GET /api/replay/{type}/{id}` | Extend with session management |
| Verification | Not implemented | New: output comparison engine |
| Timeline | Not implemented | New: unified ordered sequence |
