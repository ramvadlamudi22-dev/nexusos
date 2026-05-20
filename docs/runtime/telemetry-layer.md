# Operational Telemetry Layer

**Module:** `nexusos.runtime.telemetry`  
**Principle:** If it executes, it emits. No invisible operations.

---

## What Gets Tracked

| Category | Metrics | Purpose |
|----------|---------|---------|
| Workflow states | active, completed, failed, retrying | Execution visibility |
| Retries | count per node, per workflow, success rate | Recovery effectiveness |
| Runtime health | per-component state, transitions | System stability |
| Session integrity | corruption events, restorations | Browser reliability |
| Execution latency | per-node, per-workflow, percentiles | Performance |
| Browser stability | crashes, restarts, session count | Browser health |
| API health | response codes, latency, error rate | Backend stability |
| Replay consistency | match rate, divergence count | Determinism confidence |
| Orchestration decisions | scheduling, parallelism, queuing | Orchestration visibility |

---

## Telemetry Schema

### Execution Metrics

```typescript
interface ExecutionMetrics {
  // Counters (monotonically increasing)
  workflows_started: number;
  workflows_completed: number;
  workflows_failed: number;
  nodes_executed: number;
  nodes_retried: number;
  recoveries_attempted: number;
  recoveries_succeeded: number;
  artifacts_produced: number;
  governance_decisions: number;
  governance_denials: number;
  
  // Gauges (current value)
  active_workflows: number;
  active_browser_sessions: number;
  active_terminal_sessions: number;
  health_score: number;            // 0-100
  
  // Histograms (distribution)
  workflow_duration_ms: Histogram;
  node_duration_ms: Histogram;
  api_response_ms: Histogram;
  page_load_ms: Histogram;
  recovery_duration_ms: Histogram;
}
```

### Health Telemetry

```typescript
interface HealthTelemetry {
  timestamp: string;
  overall: "HEALTHY" | "DEGRADED" | "UNHEALTHY";
  components: Record<string, {
    state: HealthState;
    last_check: string;
    consecutive_failures: number;
    uptime_percent: number;        // Over last hour
    error_rate: number;            // Over last 5 minutes
  }>;
  
  // Derived
  mean_time_between_failures_ms: number;
  mean_time_to_recovery_ms: number;
  availability_percent: number;    // Over last 24 hours
}
```

### Session Telemetry

```typescript
interface SessionTelemetry {
  session_id: string;
  type: "BROWSER" | "TERMINAL";
  
  // Lifecycle
  created_at: string;
  state: string;
  duration_ms: number;
  
  // Operations
  operations_count: number;
  operations_failed: number;
  
  // Browser-specific
  pages_navigated: number;
  screenshots_captured: number;
  console_errors: number;
  network_requests: number;
  network_failures: number;
  
  // Stability
  corruptions_detected: number;
  restorations_performed: number;
  crashes: number;
}
```

---

## Event Stream

All telemetry flows through a structured event stream:

```typescript
interface TelemetryEvent {
  id: string;
  timestamp: string;
  category: TelemetryCategory;
  event_type: string;
  source: string;                  // Component that emitted
  execution_id: string | null;     // Correlation
  
  // Payload varies by event type
  payload: Record<string, unknown>;
  
  // Severity for alerting
  severity: "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";
}

enum TelemetryCategory {
  EXECUTION  = "execution",
  HEALTH     = "health",
  BROWSER    = "browser",
  NETWORK    = "network",
  GOVERNANCE = "governance",
  RECOVERY   = "recovery",
  ARTIFACT   = "artifact",
  REPLAY     = "replay",
}
```

### Key Events

| Event | Category | Severity | Trigger |
|-------|----------|----------|---------|
| `workflow.started` | execution | INFO | Workflow begins |
| `workflow.completed` | execution | INFO | Workflow succeeds |
| `workflow.failed` | execution | ERROR | Workflow fails |
| `node.retry` | execution | WARNING | Node being retried |
| `health.degraded` | health | WARNING | Component degraded |
| `health.unhealthy` | health | ERROR | Component failed |
| `health.recovered` | health | INFO | Component restored |
| `browser.crash` | browser | ERROR | Browser process died |
| `browser.restored` | browser | INFO | Browser restarted |
| `session.corrupted` | browser | WARNING | Session state invalid |
| `governance.denied` | governance | WARNING | Action blocked |
| `recovery.started` | recovery | INFO | Recovery initiated |
| `recovery.succeeded` | recovery | INFO | Recovery worked |
| `recovery.failed` | recovery | ERROR | Recovery didn't work |
| `replay.diverged` | replay | ERROR | Replay doesn't match |
| `artifact.produced` | artifact | DEBUG | New artifact stored |

---

## Execution Latency Tracking

```
Workflow Execution Timeline:
┌─────────────────────────────────────────────────────────────┐
│ Total: 12.5s                                                 │
│                                                             │
│ ├── Pre-flight: 0.5s                                        │
│ ├── Node: check-homepage: 1.2s                              │
│ │   ├── Navigate: 0.8s                                      │
│ │   ├── Wait: 0.2s                                          │
│ │   └── Screenshot: 0.2s                                    │
│ ├── Node: check-dashboard: 2.1s                             │
│ │   ├── Navigate: 1.5s                                      │
│ │   ├── Wait: 0.3s                                          │
│ │   └── Screenshot: 0.3s                                    │
│ ├── Node: check-api-health: 0.1s                            │
│ ├── Node: check-api-users: 0.2s                             │
│ ├── Node: record-video: 8.0s (parallel with page checks)    │
│ └── Node: generate-report: 0.4s                             │
│                                                             │
│ Critical path: pre-flight → video recording → report        │
│ Parallelism efficiency: 65%                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Replay Consistency Metrics

```typescript
interface ReplayConsistencyMetrics {
  total_replays: number;
  identical_replays: number;       // Byte-for-byte match
  equivalent_replays: number;      // Logically same
  diverged_replays: number;        // Different results
  
  // Rates
  determinism_rate: number;        // identical / total
  consistency_rate: number;        // (identical + equivalent) / total
  
  // Divergence analysis
  common_divergence_causes: {
    cause: string;
    count: number;
    percentage: number;
  }[];
}
```

---

## Telemetry API

```
GET  /api/telemetry/metrics              → Current metric values
GET  /api/telemetry/health               → Component health states
GET  /api/telemetry/events?since=T       → Event stream (filtered)
GET  /api/telemetry/executions           → Execution telemetry
GET  /api/telemetry/sessions             → Session telemetry
GET  /api/telemetry/latency/{exec_id}    → Execution latency breakdown
GET  /api/telemetry/replay/consistency   → Replay consistency metrics
GET  /api/telemetry/dashboard            → Bundled dashboard data
```

---

## Mapping to Current Implementation

| Concept | Existing | Gap |
|---------|----------|-----|
| Metric recording | `TelemetryCollector.record_metric()` | Add histograms, labels |
| Counters | `TelemetryCollector.increment_counter()` | ✓ Working |
| Health states | `RuntimeHealthMonitor` | Add uptime tracking |
| Event dispatch | `EventBus.dispatch()` | Add categories, severity |
| Execution telemetry | `ExecutionTelemetryCollector` | Add latency breakdown |
| Session tracking | `BrowserRuntime`, `TerminalRuntime` | Add stability metrics |
| API endpoints | `/api/telemetry/*` | Extend with new endpoints |
| Dashboard data | Frontend fetches individually | Add bundled endpoint |
