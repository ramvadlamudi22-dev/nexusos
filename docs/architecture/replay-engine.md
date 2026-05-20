# Replay Engine

**Module:** `nexusos.replay`  
**Status:** Architecture Specification  
**Principle:** Every execution must be reconstructable from recorded inputs

---

## Overview

The Replay Engine enables deterministic reconstruction of any past execution. Given the same recorded inputs, time source, and configuration, replay produces identical outputs. Divergence between original execution and replay constitutes a system defect.

---

## Replay Model

```
┌─────────────────────────────────────────────────────────┐
│                    ReplaySession                          │
├─────────────────────────────────────────────────────────┤
│  id: string                                              │
│  source_execution_id: string                             │
│  state: LOADING | REPLAYING | PAUSED | COMPLETED | ERROR │
│  timeline: ReplayTimeline                                │
│  time_source: RecordedTimeSource                         │
│  artifacts: ArtifactIndex                                │
│  checkpoints: Checkpoint[]                               │
│  current_position: TimelinePosition                      │
└─────────────────────────────────────────────────────────┘
```

---

## What Gets Recorded

### Browser Actions
```
┌────────────────────────────────────────────┐
│  BrowserRecord                              │
├────────────────────────────────────────────┤
│  session_id: string                         │
│  timestamp: ISO string                      │
│  action: {type, target, value, ...}         │
│  result: {success, screenshot_ref, ...}     │
│  dom_snapshot_ref: string                   │
│  network_log_ref: string                    │
└────────────────────────────────────────────┘
```

### Terminal Commands
```
┌────────────────────────────────────────────┐
│  TerminalRecord                             │
├────────────────────────────────────────────┤
│  session_id: string                         │
│  timestamp: ISO string                      │
│  command: string                            │
│  stdout: string                             │
│  stderr: string                             │
│  exit_code: number                          │
│  duration_ms: number                        │
│  environment: Record<string, string>        │
└────────────────────────────────────────────┘
```

### Workflow Executions
```
┌────────────────────────────────────────────┐
│  WorkflowRecord                             │
├────────────────────────────────────────────┤
│  execution_id: string                       │
│  graph_definition: ExecutionGraph           │
│  step_results: StepResult[]                 │
│  state_transitions: StateTransition[]       │
│  governance_decisions: GovernanceDecision[]  │
│  telemetry: ExecutionTelemetry              │
└────────────────────────────────────────────┘
```

### Telemetry & Traces
```
┌────────────────────────────────────────────┐
│  TelemetryRecord                            │
├────────────────────────────────────────────┤
│  metrics: MetricRecord[]                    │
│  traces: TraceRecord[]                      │
│  counters: Record<string, number>           │
│  health_transitions: HealthTransition[]     │
└────────────────────────────────────────────┘
```

---

## Timeline Reconstruction

The replay timeline is an ordered sequence of all recorded operations:

```
Timeline:
  T+0ms     [WORKFLOW] Graph registered
  T+1ms     [GOVERNANCE] Action validated → permitted
  T+2ms     [EVENT] RUNTIME event dispatched (seq: 1)
  T+5ms     [WORKFLOW] Step "init" started
  T+105ms   [WORKFLOW] Step "init" completed
  T+106ms   [WORKFLOW] Step "validate" started
  T+106ms   [WORKFLOW] Step "execute" started (parallel)
  T+306ms   [WORKFLOW] Step "validate" completed
  T+4606ms  [BROWSER] Action executed in session
  T+4607ms  [WORKFLOW] Step "execute" completed
  T+4608ms  [WORKFLOW] Step "aggregate" started
  T+4808ms  [WORKFLOW] Step "aggregate" completed
  T+4809ms  [TELEMETRY] Metrics recorded
```

---

## Replay Modes

### Full Replay
Reconstructs the entire execution from start to finish using the recorded time source. Verifies all outputs match.

### Partial Replay
Replays from a checkpoint to a specific point. Useful for debugging failures.

### Differential Replay
Replays with a modified graph/config and compares outputs to the original. Identifies behavioral changes.

### Stepped Replay
Advances one operation at a time, allowing inspection at each step.

---

## Recorded Time Source

```python
class RecordedTimeSource:
    """Replays timestamps from a recorded execution."""
    
    def __init__(self, timestamps: List[float]):
        self._timestamps = timestamps
        self._index = 0
    
    def __call__(self) -> float:
        ts = self._timestamps[self._index]
        self._index += 1
        return ts
```

Injected into `RuntimeExecutionContext` during replay, ensuring all time-dependent operations produce identical results.

---

## Replay Storage Topology

```
replay/
├── sessions/
│   └── {session_id}/
│       ├── manifest.json          (session metadata)
│       ├── timeline.jsonl         (ordered operations)
│       ├── browser/
│       │   ├── actions.jsonl      (browser action log)
│       │   ├── screenshots/       (captured screenshots)
│       │   └── dom-snapshots/     (DOM state captures)
│       ├── terminal/
│       │   └── commands.jsonl     (terminal command log)
│       ├── workflows/
│       │   └── {execution_id}.json (workflow execution record)
│       ├── telemetry/
│       │   ├── metrics.jsonl      (metric records)
│       │   └── traces.jsonl       (trace records)
│       ├── governance/
│       │   └── decisions.jsonl    (governance audit log)
│       └── checkpoints/
│           └── {checkpoint_id}.json (state snapshot)
└── index.json                     (session index)
```

---

## Replay API

```
GET  /api/replay/sessions                    → List replay sessions
GET  /api/replay/sessions/{id}               → Get session metadata
GET  /api/replay/sessions/{id}/timeline      → Get full timeline
GET  /api/replay/sessions/{id}/timeline?from=T1&to=T2  → Time range
POST /api/replay/sessions/{id}/start         → Begin replay
POST /api/replay/sessions/{id}/pause         → Pause replay
POST /api/replay/sessions/{id}/step          → Advance one operation
POST /api/replay/sessions/{id}/seek?position=T  → Seek to position
GET  /api/replay/sessions/{id}/state         → Current replay state
GET  /api/replay/sessions/{id}/artifacts     → Linked artifacts
GET  /api/replay/sessions/{id}/diff?compare={other_id}  → Differential
```

---

## Replay Verification

After replay completes, the engine compares:
1. All node outputs (byte-level comparison)
2. All state transitions (sequence and timing)
3. All governance decisions (same policy → same outcome)
4. All telemetry values (counters, metrics)

Divergence report:
```json
{
  "replay_id": "rpl-001",
  "source_execution_id": "exec-001",
  "verdict": "MATCH" | "DIVERGED",
  "divergences": [
    {
      "position": "T+4606ms",
      "operation": "browser_action",
      "expected": {"success": true},
      "actual": {"success": false},
      "cause": "external_dependency_changed"
    }
  ]
}
```

---

## Integration with Existing Code

| Architecture Component | Current Implementation |
|----------------------|----------------------|
| ReplayRecorder | `backend/replay/recorder.py` |
| ExecutionReplayManager | `backend/replay/execution.py` |
| Browser session recording | `BrowserRuntime.recording` list |
| Terminal session recording | `TerminalSession.command_history` |
| Replay API | `GET /api/replay/{session_type}/{session_id}` |
| Time injection | `RuntimeExecutionContext(time_source=...)` |

Evolution extends with: timeline reconstruction, stepped replay, differential comparison, and verification.
