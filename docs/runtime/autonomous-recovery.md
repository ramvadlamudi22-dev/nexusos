# Autonomous Recovery Engine

**Module:** `nexusos.runtime.recovery`  
**Version:** 2.0  
**Principle:** The system detects, classifies, and recovers from failures without human intervention

---

## Design Intent

The Autonomous Recovery Engine provides self-healing capabilities that detect degradation before it becomes failure, classify failures by severity and recoverability, and execute governed recovery procedures. Recovery is not an afterthought — it is a first-class runtime operation subject to the same governance, telemetry, and replay guarantees as any other execution.

---

## Failure Classification

```
┌─────────────────────────────────────────────────────────────┐
│                    Failure Taxonomy                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Level 0: ANOMALY                                           │
│  ├── Elevated latency (>2x baseline, <5x)                  │
│  ├── Sporadic errors (<5% error rate)                       │
│  └── Recovery: Monitor + alert (no action)                  │
│                                                             │
│  Level 1: TRANSIENT                                         │
│  ├── Single request timeout                                 │
│  ├── Temporary connection refused                           │
│  ├── DNS resolution delay                                   │
│  └── Recovery: Automatic retry with backoff                 │
│                                                             │
│  Level 2: DEGRADED                                          │
│  ├── Sustained elevated error rate (>10%)                   │
│  ├── Latency >5x baseline                                  │
│  ├── Partial functionality loss                             │
│  └── Recovery: Circuit breaker + traffic shaping            │
│                                                             │
│  Level 3: COMPONENT_FAILURE                                 │
│  ├── Health check failing consecutively                     │
│  ├── Component unresponsive                                 │
│  ├── OOM or resource exhaustion                             │
│  └── Recovery: Component restart + state recovery           │
│                                                             │
│  Level 4: CASCADE                                           │
│  ├── Multiple dependent components failing                  │
│  ├── Failure propagating through dependency graph           │
│  ├── System-wide degradation                                │
│  └── Recovery: Orchestrated restart sequence                │
│                                                             │
│  Level 5: INTEGRITY                                         │
│  ├── Data corruption detected                               │
│  ├── Governance bypass detected                             │
│  ├── Audit trail inconsistency                              │
│  └── Recovery: HALT (no autonomous recovery)                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Detection Engine

```typescript
interface DetectionRule {
  id: string;
  name: string;
  component: string;
  condition: DetectionCondition;
  severity: FailureLevel;
  cooldown_ms: number;             // Minimum time between triggers
  requires_consecutive: number;    // Consecutive failures before trigger
}

interface DetectionCondition {
  type: "THRESHOLD" | "RATE" | "PATTERN" | "ABSENCE";
  metric: string;                  // Metric name to evaluate
  operator: "GT" | "LT" | "EQ" | "RATE_ABOVE" | "MISSING_FOR";
  value: number;
  window_ms: number;              // Evaluation window
}
```

### Built-in Detection Rules

| Rule | Condition | Level |
|------|-----------|-------|
| API timeout | response_time > 5000ms for 3 consecutive | TRANSIENT |
| Error rate spike | error_rate > 0.10 over 60s window | DEGRADED |
| Health check fail | health_check = false for 3 consecutive | COMPONENT_FAILURE |
| Multi-component fail | 2+ components UNHEALTHY simultaneously | CASCADE |
| Audit checksum mismatch | checksum_valid = false | INTEGRITY |
| Memory pressure | memory_used > 90% | DEGRADED |
| Event bus stall | events_processed = 0 for 30s | COMPONENT_FAILURE |

---

## Recovery Strategies

### Strategy: Retry

```typescript
interface RetryStrategy {
  type: "RETRY";
  max_attempts: number;
  backoff: BackoffConfig;
  scope: "OPERATION" | "REQUEST";
}
```

Applied to: Level 1 (TRANSIENT) failures.

### Strategy: Circuit Breaker

```typescript
interface CircuitBreakerStrategy {
  type: "CIRCUIT_BREAKER";
  failure_threshold: number;       // Failures before opening
  success_threshold: number;       // Successes to close
  timeout_ms: number;             // Time in open state before half-open
  half_open_max_requests: number;
}
```

Applied to: Level 2 (DEGRADED) failures.

### Strategy: Component Restart

```typescript
interface RestartStrategy {
  type: "RESTART";
  target: string;                  // Component identifier
  graceful_shutdown_ms: number;
  startup_timeout_ms: number;
  verify_health: boolean;
  max_restart_attempts: number;
  restart_cooldown_ms: number;
}
```

Applied to: Level 3 (COMPONENT_FAILURE) failures.

### Strategy: Orchestrated Recovery

```typescript
interface OrchestratedStrategy {
  type: "ORCHESTRATED";
  steps: RecoveryStep[];
  rollback_on_failure: boolean;
  governance_required: boolean;
}

interface RecoveryStep {
  action: "DRAIN" | "STOP" | "RESTART" | "WAIT_HEALTHY" | 
          "VERIFY_API" | "RESTORE_TRAFFIC" | "CHECKPOINT";
  target: string;
  timeout_ms: number;
  params: Record<string, unknown>;
}
```

Applied to: Level 4 (CASCADE) failures.

---

## Recovery Orchestration Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Detect  │───→│ Classify │───→│   Plan   │───→│ Govern   │
│          │    │          │    │          │    │          │
│ anomaly  │    │ taxonomy │    │ strategy │    │ validate │
│ threshold│    │ level    │    │ select   │    │ approve  │
│ pattern  │    │ scope    │    │ params   │    │ audit    │
└──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                      │
                                                      │ permitted
                                                      ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Record  │◄───│  Verify  │◄───│ Execute  │◄───│ Prepare  │
│          │    │          │    │          │    │          │
│ outcome  │    │ health   │    │ strategy │    │ isolate  │
│ telemetry│    │ restored │    │ steps    │    │ snapshot │
│ replay   │    │ stable   │    │ monitor  │    │ drain    │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## Degraded Mode Handling

When full recovery is not immediately possible, the system enters degraded mode:

```typescript
interface DegradedModeConfig {
  component: string;
  fallback_behavior: "CACHED_RESPONSE" | "PARTIAL_FUNCTION" | 
                     "QUEUE_REQUESTS" | "REJECT_GRACEFULLY";
  max_duration_ms: number;         // Auto-escalate after this
  notify: boolean;
  reduced_capabilities: string[];  // What's unavailable
}
```

Example: If the browser runtime fails, the system continues operating with terminal and workflow capabilities while browser recovery proceeds.

---

## Runtime Diagnostics Pipeline

When a failure is detected, diagnostics collect:

```typescript
interface DiagnosticReport {
  id: string;
  timestamp: string;
  failure_level: FailureLevel;
  affected_component: string;
  
  // Context
  health_snapshot: Record<string, HealthState>;
  recent_errors: ErrorEntry[];
  dependency_states: Record<string, HealthState>;
  
  // Telemetry window
  metrics_window: MetricSnapshot[];  // Last 5 minutes
  event_window: RuntimeEvent[];      // Last 100 events
  trace_window: Trace[];             // Active traces
  
  // Analysis
  probable_cause: string;
  affected_executions: string[];
  recommended_action: RecoveryStrategy;
  
  // Metadata
  previous_recoveries: RecoveryRecord[];
  time_since_last_healthy_ms: number;
}
```

---

## Governed Recovery

All recovery actions pass through governance:

| Action | Required Permission | Governance Behavior |
|--------|-------------------|-------------------|
| Retry operation | `recovery.retry` | Auto-approve (Level 1) |
| Open circuit breaker | `recovery.circuit_break` | Auto-approve (Level 2) |
| Restart component | `recovery.restart` | Validate + audit |
| Orchestrated recovery | `recovery.orchestrate` | Validate + audit |
| HALT system | N/A | Unconditional (Level 5) |

Recovery actions that governance denies are:
1. Logged in audit trail
2. Escalated to next level
3. If all levels exhausted → HALT

---

## Mapping to Current Implementation

| New Concept | Existing Code | Gap |
|-------------|--------------|-----|
| Health monitoring | `RuntimeHealthMonitor` | Add detection rules, thresholds |
| Health states | `HealthState` enum | Already has HEALTHY/DEGRADED/UNHEALTHY |
| Component tracking | `update_component()` | Add dependency graph |
| Docker healthcheck | `curl /api/health` | Already implemented |
| Container restart | `docker compose restart` | Validated in containerization |
| Governance validation | `GovernanceEngine` | Add recovery-specific policies |
| Audit recording | `AuditLogger` | Already records all decisions |
| Telemetry | `TelemetryCollector` | Add windowed queries |
