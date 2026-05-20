# Runtime Observability

**Module:** `nexusos.runtime.observability`  
**Version:** 2.0  
**Principle:** No black-box execution. All internal decision paths are inspectable.

---

## Design Intent

Runtime Observability transforms NexusOS from a system that logs events into a system where every execution path is a first-class observable entity. Telemetry is not bolted on — it is structural. Every node execution, governance decision, state transition, and artifact production emits structured telemetry that feeds dashboards, alerting, replay, and self-healing.

---

## Telemetry Pipeline Architecture

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Emitters  │──→│  Collector  │──→│  Processor  │──→│   Storage   │
│             │   │             │   │             │   │             │
│ Every node  │   │ Buffer      │   │ Aggregate   │   │ Time-series │
│ Every edge  │   │ Validate    │   │ Enrich      │   │ Event log   │
│ Every gate  │   │ Sequence    │   │ Correlate   │   │ Trace store │
└─────────────┘   └─────────────┘   └─────────────┘   └──────┬──────┘
                                                              │
                                              ┌───────────────┼───────────────┐
                                              │               │               │
                                              ▼               ▼               ▼
                                        ┌───────────┐  ┌───────────┐  ┌───────────┐
                                        │ Dashboard │  │  Alerting │  │  Replay   │
                                        │           │  │           │  │  Engine   │
                                        │ Real-time │  │ Threshold │  │           │
                                        │ widgets   │  │ Anomaly   │  │ Timeline  │
                                        └───────────┘  └───────────┘  └───────────┘
```

---

## Event Stream Architecture

### Stream Channels

```typescript
interface EventChannel {
  name: string;                    // e.g., "execution.node.*"
  pattern: string;                 // Glob pattern for subscription
  retention_hours: number;
  max_buffer_size: number;
  delivery_guarantee: "AT_LEAST_ONCE" | "EXACTLY_ONCE";
}
```

| Channel | Events | Retention |
|---------|--------|-----------|
| `execution.graph.*` | Graph lifecycle (start, complete, fail) | 168h |
| `execution.node.*` | Node state transitions | 168h |
| `governance.*` | Policy decisions, audit records | Forever |
| `health.*` | Component health transitions | 72h |
| `browser.*` | Session lifecycle, actions | 72h |
| `terminal.*` | Command executions | 72h |
| `telemetry.*` | Metric emissions, trace completions | 24h |
| `recovery.*` | Failure detection, recovery actions | 168h |
| `artifact.*` | Artifact creation, indexing | 168h |

### Event Schema

```typescript
interface RuntimeEvent {
  id: string;                      // Deterministic (SHA-256)
  channel: string;
  type: string;                    // e.g., "node.state_changed"
  timestamp: string;               // ISO from execution context
  sequence: number;                // Monotonic per channel
  source_component: string;
  execution_id: string | null;     // Correlation to execution
  trace_id: string | null;         // Correlation to trace
  payload: Record<string, unknown>;
  checksum: string;                // Integrity verification
}
```

---

## Execution Timelines

A unified chronological view of all operations within an execution:

```typescript
interface ExecutionTimeline {
  execution_id: string;
  graph_id: string;
  start_time: string;
  end_time: string;
  entries: TimelineEntry[];
}

interface TimelineEntry {
  offset_ms: number;               // Milliseconds from execution start
  category: "GRAPH" | "NODE" | "GOVERNANCE" | "BROWSER" | 
            "TERMINAL" | "TELEMETRY" | "EVENT" | "ARTIFACT";
  operation: string;
  details: Record<string, unknown>;
  duration_ms: number | null;      // For operations with duration
  trace_span_id: string | null;
}
```

### Timeline Rendering

```
exec-001 | Diamond Pipeline | 4.8s total
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 0ms   ┃ [GRAPH] Execution started
 1ms   ┃ [GOV]   validate workflow_execution → permitted
 2ms   ┃ [NODE]  init → RUNNING
 102ms ┃ [NODE]  init → COMPLETED (100ms)
 103ms ┃ [NODE]  validate → RUNNING ─────────────────┐
 103ms ┃ [NODE]  execute → RUNNING ──────────────┐   │ parallel
 110ms ┃ [GOV]   validate browser_action → ok    │   │
 115ms ┃ [BRW]   navigate https://example.com    │   │
 303ms ┃ [NODE]  validate → COMPLETED (200ms) ───┘   │
4500ms ┃ [BRW]   screenshot captured                  │
4603ms ┃ [NODE]  execute → COMPLETED (4500ms) ────────┘
4604ms ┃ [NODE]  aggregate → RUNNING
4804ms ┃ [NODE]  aggregate → COMPLETED (200ms)
4805ms ┃ [TEL]   metrics recorded (4 counters)
4806ms ┃ [ART]   execution manifest produced
4807ms ┃ [GRAPH] Execution COMPLETED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Distributed Traces

### Trace Structure

```typescript
interface Trace {
  trace_id: string;                // Propagated across all components
  root_span_id: string;
  spans: Span[];
  start_time: string;
  end_time: string;
  status: "OK" | "ERROR";
  attributes: Record<string, string>;
}

interface Span {
  span_id: string;
  parent_span_id: string | null;
  operation_name: string;
  component: string;
  start_time: string;
  end_time: string;
  status: "OK" | "ERROR";
  attributes: Record<string, string>;
  events: SpanEvent[];
  links: SpanLink[];               // Cross-trace references
}
```

### Trace Propagation

```
API Request (trace_id created)
  └── Workflow Execution (child span)
       ├── Governance Validation (child span)
       ├── Node: init (child span)
       ├── Node: validate (child span)
       │    └── Governance Check (child span)
       ├── Node: execute (child span)
       │    ├── Browser Session (child span)
       │    │    ├── Navigate (child span)
       │    │    └── Screenshot (child span)
       │    └── Telemetry Record (child span)
       └── Node: aggregate (child span)
            └── Artifact Store (child span)
```

---

## Runtime Metrics

### Metric Types

```typescript
type MetricType = "COUNTER" | "GAUGE" | "HISTOGRAM" | "SUMMARY";

interface MetricDefinition {
  name: string;
  type: MetricType;
  description: string;
  labels: string[];
  unit: string;
  buckets?: number[];              // For histograms
}
```

### Core Metrics

| Metric | Type | Labels | Unit |
|--------|------|--------|------|
| `nexusos_executions_total` | Counter | graph_id, state | count |
| `nexusos_node_duration_ms` | Histogram | node_type, state | ms |
| `nexusos_governance_decisions` | Counter | action, outcome | count |
| `nexusos_health_state` | Gauge | component | enum |
| `nexusos_active_sessions` | Gauge | runtime_type | count |
| `nexusos_retry_attempts` | Counter | node_id, attempt | count |
| `nexusos_checkpoint_size_bytes` | Histogram | — | bytes |
| `nexusos_artifact_count` | Counter | type | count |
| `nexusos_event_bus_depth` | Gauge | channel | count |
| `nexusos_recovery_actions` | Counter | level, outcome | count |

---

## Browser Telemetry

```typescript
interface BrowserTelemetry {
  session_id: string;
  page_loads: number;
  actions_executed: number;
  actions_failed: number;
  screenshots_captured: number;
  network_requests: number;
  network_errors: number;
  javascript_errors: number;
  dom_mutations: number;
  total_duration_ms: number;
  page_load_times_ms: number[];    // Per navigation
  action_durations_ms: number[];   // Per action
}
```

---

## Observability API

```
GET  /api/observability/timeline/{execution_id}     → Unified timeline
GET  /api/observability/traces                      → Recent traces
GET  /api/observability/traces/{trace_id}           → Full trace with spans
GET  /api/observability/metrics                     → Current metric values
GET  /api/observability/metrics/{name}              → Specific metric history
GET  /api/observability/events?channel=X&since=T    → Filtered event stream
GET  /api/observability/health/graph                → Health dependency graph
GET  /api/observability/dashboard                   → Dashboard data bundle
```

---

## Dashboard Data Model

```typescript
interface DashboardState {
  system_health: {
    overall: HealthState;
    components: Record<string, HealthState>;
  };
  execution_summary: {
    active: number;
    completed_24h: number;
    failed_24h: number;
    avg_duration_ms: number;
  };
  governance_summary: {
    decisions_24h: number;
    denied_24h: number;
    policies_active: number;
  };
  telemetry_summary: {
    events_per_minute: number;
    error_rate: number;
    p99_latency_ms: number;
  };
  recent_events: RuntimeEvent[];
}
```

---

## Mapping to Current Implementation

| New Concept | Existing Code | Gap |
|-------------|--------------|-----|
| Event channels | `EventBus` (single channel) | Add multi-channel with patterns |
| Traces | `TelemetryCollector.start_trace()` | Add spans, propagation, linking |
| Metrics | `TelemetryCollector.record_metric()` | Add histograms, labels, aggregation |
| Timeline | Not implemented | New: unified chronological view |
| Dashboard data | Frontend components fetch individually | Add bundled dashboard endpoint |
| Health graph | `RuntimeHealthMonitor` | Add dependency edges |
| Browser telemetry | `ExecutionTelemetryCollector` | Add per-session detail |
