# Telemetry Runtime

**Module:** `nexusos.telemetry`  
**Status:** Architecture Specification  
**Principle:** Every system action is observable, traceable, and auditable

---

## Overview

The Telemetry Runtime provides comprehensive operational intelligence through structured metrics, distributed traces, event streams, and execution timelines. No operation is invisible. All telemetry is explicit, inspectable, and feeds into the self-healing and replay systems.

---

## Telemetry Pipeline

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Emit    │───→│ Collect  │───→│Aggregate │───→│  Store   │
│          │    │          │    │          │    │          │
│ metrics  │    │ buffer   │    │ window   │    │ persist  │
│ traces   │    │ validate │    │ compute  │    │ index    │
│ events   │    │ enrich   │    │ rollup   │    │ expire   │
└──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                      │
                                              ┌───────┴───────┐
                                              │               │
                                              ▼               ▼
                                        ┌──────────┐   ┌──────────┐
                                        │  Query   │   │  Alert   │
                                        │          │   │          │
                                        │ dashboard│   │ threshold│
                                        │ API      │   │ anomaly  │
                                        └──────────┘   └──────────┘
```

---

## Metrics Schema

### Counter Metrics
```
┌────────────────────────────────────────────────────────┐
│  Name                          │ Labels                  │
├────────────────────────────────┼─────────────────────────┤
│  operations.total              │ runtime, type           │
│  operations.errors             │ runtime, error_type     │
│  governance.decisions          │ outcome (permit/deny)   │
│  workflow.executions           │ state (completed/failed)│
│  browser.actions               │ action_type             │
│  terminal.commands             │ exit_code_class         │
│  replay.sessions               │ state                   │
│  artifacts.produced            │ type                    │
└────────────────────────────────┴─────────────────────────┘
```

### Gauge Metrics
```
┌────────────────────────────────────────────────────────┐
│  Name                          │ Labels                  │
├────────────────────────────────┼─────────────────────────┤
│  health.overall                │ —                       │
│  health.component              │ component_name          │
│  sessions.active               │ runtime (browser/term)  │
│  workflows.running             │ —                       │
│  memory.used_bytes             │ component               │
│  event_bus.queue_depth         │ —                       │
└────────────────────────────────┴─────────────────────────┘
```

### Histogram Metrics
```
┌────────────────────────────────────────────────────────┐
│  Name                          │ Buckets                 │
├────────────────────────────────┼─────────────────────────┤
│  operation.duration_ms         │ 10,50,100,500,1000,5000 │
│  workflow.step_duration_ms     │ 10,50,100,500,1000,5000 │
│  browser.action_duration_ms    │ 50,100,500,1000,5000    │
│  api.response_time_ms          │ 5,10,50,100,500         │
└────────────────────────────────┴─────────────────────────┘
```

---

## Distributed Traces

```
┌─────────────────────────────────────────────────────────┐
│                      Trace                               │
├─────────────────────────────────────────────────────────┤
│  trace_id: string (propagated across components)         │
│  spans: Span[]                                           │
│  root_operation: string                                  │
│  start_time: ISO string                                  │
│  end_time: ISO string                                    │
│  status: OK | ERROR                                      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                       Span                               │
├─────────────────────────────────────────────────────────┤
│  span_id: string                                         │
│  parent_span_id: string (null for root)                  │
│  operation: string                                       │
│  component: string                                       │
│  start_time: ISO string                                  │
│  end_time: ISO string                                    │
│  status: OK | ERROR                                      │
│  attributes: Record<string, string>                      │
│  events: SpanEvent[]                                     │
└─────────────────────────────────────────────────────────┘
```

### Trace Example: Workflow Execution

```
Trace: wf-exec-001
├── [Span] workflow.execute (root)
│   ├── [Span] governance.validate
│   │   └── [Event] decision: permitted
│   ├── [Span] workflow.step.init
│   │   └── [Event] step_completed
│   ├── [Span] workflow.step.validate (parallel)
│   │   ├── [Span] governance.validate
│   │   └── [Event] step_completed
│   ├── [Span] workflow.step.execute (parallel)
│   │   ├── [Span] browser.action
│   │   │   └── [Event] screenshot_captured
│   │   └── [Event] step_completed
│   └── [Span] workflow.step.aggregate
│       ├── [Span] telemetry.record
│       └── [Event] step_completed
└── [Event] workflow_completed
```

---

## Event Streams

```
┌─────────────────────────────────────────────────────────┐
│                     EventStream                          │
├─────────────────────────────────────────────────────────┤
│  Channels:                                               │
│    runtime.*      — Runtime lifecycle events             │
│    workflow.*     — Workflow state transitions            │
│    governance.*   — Policy decisions                     │
│    health.*       — Health state changes                 │
│    browser.*      — Browser session events               │
│    terminal.*     — Terminal command events               │
│    recovery.*     — Self-healing events                  │
│                                                         │
│  Delivery: At-least-once, ordered by sequence            │
│  Retention: Configurable per channel                     │
│  Replay: Full stream replay from any sequence number     │
└─────────────────────────────────────────────────────────┘
```

---

## Execution Timelines

A unified timeline view combining all telemetry sources:

```
Timeline for execution exec-001:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
T+0ms    │ [GOV] validate workflow → permitted
T+1ms    │ [WF]  execution started
T+2ms    │ [EVT] RUNTIME event (seq: 1)
T+5ms    │ [WF]  step "init" → RUNNING
T+105ms  │ [WF]  step "init" → COMPLETED (100ms)
T+106ms  │ [WF]  step "validate" → RUNNING
T+106ms  │ [WF]  step "execute" → RUNNING
T+110ms  │ [GOV] validate browser_action → permitted
T+115ms  │ [BRW] navigate to https://example.com
T+4500ms │ [BRW] screenshot captured
T+4600ms │ [WF]  step "execute" → COMPLETED (4494ms)
T+306ms  │ [WF]  step "validate" → COMPLETED (200ms)
T+4601ms │ [WF]  step "aggregate" → RUNNING
T+4801ms │ [WF]  step "aggregate" → COMPLETED (200ms)
T+4802ms │ [TEL] metrics recorded
T+4803ms │ [WF]  execution → COMPLETED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Observability API

```
GET  /api/telemetry/metrics              → All metrics
GET  /api/telemetry/metrics?name=X       → Specific metric
GET  /api/telemetry/traces               → Recent traces
GET  /api/telemetry/traces/{trace_id}    → Specific trace with spans
GET  /api/telemetry/health               → Component health states
GET  /api/telemetry/executions           → Execution telemetry
GET  /api/telemetry/timeline/{exec_id}   → Unified execution timeline
GET  /api/events                         → Event stream
GET  /api/events?channel=workflow.*       → Filtered events
```

---

## Integration with Existing Code

| Architecture Component | Current Implementation |
|----------------------|----------------------|
| MetricRecord | `TelemetryCollector.record_metric()` |
| TraceRecord | `TelemetryCollector.start_trace()` |
| Counters | `TelemetryCollector.increment_counter()` |
| Health states | `RuntimeHealthMonitor` |
| Event stream | `EventBus.dispatch()` |
| Execution telemetry | `ExecutionTelemetryCollector` |
| Per-runtime health | `get_execution_health()` |
| API endpoints | `/api/telemetry/*`, `/api/events`, `/api/health` |

Evolution extends with: distributed traces with spans, histogram metrics, event stream channels, unified timelines, and alerting thresholds.
