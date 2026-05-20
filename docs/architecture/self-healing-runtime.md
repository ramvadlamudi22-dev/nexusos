# Self-Healing Runtime

**Module:** `nexusos.recovery`  
**Status:** Architecture Specification  
**Principle:** The system detects, diagnoses, and recovers from failures autonomously

---

## Overview

The Self-Healing Runtime provides autonomous failure detection, diagnosis, and recovery. It monitors the health graph, detects degradation, classifies failures, and executes governed recovery procedures. All recovery actions are themselves governed and recorded for replay.

---

## Health Graph

```
┌─────────────────────────────────────────────────────────┐
│                     HealthGraph                           │
├─────────────────────────────────────────────────────────┤
│  components: Map<string, ComponentHealth>                 │
│  dependencies: DependencyEdge[]                          │
│  overall_state: HEALTHY | DEGRADED | UNHEALTHY | UNKNOWN │
│  last_evaluation: ISO string                             │
│  transition_history: HealthTransition[]                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   ComponentHealth                         │
├─────────────────────────────────────────────────────────┤
│  name: string                                            │
│  state: HEALTHY | DEGRADED | UNHEALTHY | UNKNOWN         │
│  last_check: ISO string                                  │
│  error_rate: float (0.0 - 1.0)                           │
│  latency_p99_ms: number                                  │
│  consecutive_failures: number                            │
│  recovery_attempts: number                               │
│  dependencies: string[]                                  │
└─────────────────────────────────────────────────────────┘
```

### Health Propagation

```
If component X depends on component Y:
  - Y UNHEALTHY → X transitions to DEGRADED (at minimum)
  - Y HEALTHY restored → X re-evaluated independently

Propagation is upward only (dependency → dependent).
A component cannot be HEALTHY if any critical dependency is UNHEALTHY.
```

---

## Failure Taxonomy

```
┌─────────────────────────────────────────────────────────┐
│  Level 1: TRANSIENT                                      │
│  - Single request timeout                                │
│  - Temporary network blip                                │
│  - Recovery: Automatic retry (no intervention)           │
├─────────────────────────────────────────────────────────┤
│  Level 2: DEGRADED                                       │
│  - Elevated error rate (>10%)                            │
│  - Increased latency (>2x baseline)                      │
│  - Recovery: Circuit breaker + backoff                    │
├─────────────────────────────────────────────────────────┤
│  Level 3: COMPONENT_FAILURE                              │
│  - Component unresponsive                                │
│  - Health check failing                                  │
│  - Recovery: Component restart                           │
├─────────────────────────────────────────────────────────┤
│  Level 4: SYSTEM_FAILURE                                 │
│  - Multiple components failing                           │
│  - Cascading failures detected                           │
│  - Recovery: Orchestrated restart sequence               │
├─────────────────────────────────────────────────────────┤
│  Level 5: UNRECOVERABLE                                  │
│  - Data corruption detected                              │
│  - Governance integrity compromised                      │
│  - Recovery: HALT + alert (no autonomous recovery)       │
└─────────────────────────────────────────────────────────┘
```

---

## Recovery Engine

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Detect   │───→│ Classify │───→│ Plan     │───→│ Execute  │
│          │    │          │    │          │    │          │
│ health   │    │ failure  │    │ recovery │    │ governed │
│ check    │    │ taxonomy │    │ strategy │    │ actions  │
│ anomaly  │    │ level    │    │ steps    │    │ verify   │
└──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                      │
                                              ┌───────┴───────┐
                                              │               │
                                              ▼               ▼
                                        ┌──────────┐   ┌──────────┐
                                        │ Success  │   │ Escalate │
                                        │          │   │          │
                                        │ restore  │   │ next     │
                                        │ healthy  │   │ level    │
                                        └──────────┘   └──────────┘
```

---

## Recovery Strategies

### Level 1: Retry
```json
{
  "strategy": "RETRY",
  "max_attempts": 3,
  "backoff": "EXPONENTIAL",
  "base_delay_ms": 100
}
```

### Level 2: Circuit Breaker
```json
{
  "strategy": "CIRCUIT_BREAKER",
  "failure_threshold": 5,
  "recovery_timeout_ms": 30000,
  "half_open_requests": 1
}
```

### Level 3: Component Restart
```json
{
  "strategy": "RESTART",
  "target": "component_name",
  "graceful_shutdown_ms": 5000,
  "startup_timeout_ms": 15000,
  "verify_health_after": true
}
```

### Level 4: Orchestrated Recovery
```json
{
  "strategy": "ORCHESTRATED",
  "sequence": [
    {"action": "drain", "target": "frontend"},
    {"action": "restart", "target": "backend"},
    {"action": "wait_healthy", "target": "backend", "timeout_ms": 15000},
    {"action": "restart", "target": "frontend"},
    {"action": "wait_healthy", "target": "frontend", "timeout_ms": 20000},
    {"action": "verify_apis", "endpoints": ["/api/health"]},
    {"action": "restore_traffic"}
  ]
}
```

---

## Diagnostics Pipeline

When a failure is detected, the diagnostics pipeline collects:

1. **Health snapshot** — Current state of all components
2. **Error context** — Recent errors, stack traces, request logs
3. **Dependency state** — Health of upstream/downstream components
4. **Telemetry window** — Metrics from the last 5 minutes
5. **Recent changes** — Any configuration or deployment changes
6. **Recovery history** — Previous recovery attempts for this component

This produces a `DiagnosticReport` artifact stored for analysis.

---

## Recovery Loops

```
┌─────────────────────────────────────────────────────────┐
│                   Recovery Loop                           │
│                                                         │
│  while (component.state != HEALTHY):                     │
│    1. Run diagnostics                                    │
│    2. Select recovery strategy (based on failure level)  │
│    3. Validate strategy with governance                  │
│    4. Execute recovery action                            │
│    5. Wait for stabilization                             │
│    6. Re-evaluate health                                 │
│    7. If still unhealthy: escalate to next level         │
│    8. If max level reached: HALT and alert               │
│                                                         │
│  Record: all actions, decisions, outcomes                │
│  Governance: every recovery action is validated          │
│  Replay: full recovery sequence is replayable            │
└─────────────────────────────────────────────────────────┘
```

---

## Governed Recovery

All recovery actions pass through governance:
- Restart operations require `recovery.restart` permission
- Orchestrated recovery requires `recovery.orchestrate` permission
- Level 5 (HALT) requires no permission — it is unconditional

Recovery actions that governance denies are logged and escalated to manual intervention.

---

## Integration with Existing Code

| Architecture Component | Current Implementation |
|----------------------|----------------------|
| Health monitoring | `RuntimeHealthMonitor` (backend/telemetry/health.py) |
| Component health | `HealthState` enum (HEALTHY, DEGRADED, UNHEALTHY, UNKNOWN) |
| Health recomputation | `_recompute_overall()` method |
| Health API | `GET /api/health`, `GET /api/telemetry/health` |
| Docker healthchecks | `curl /api/health` in Dockerfile |
| Restart recovery | `docker compose restart` (validated in containerization phase) |

Evolution extends with: failure taxonomy, recovery strategies, diagnostics pipeline, governed recovery loops, and escalation.
