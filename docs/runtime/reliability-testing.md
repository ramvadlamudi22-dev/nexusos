# Execution Reliability Testing

**Module:** `nexusos.runtime.reliability`  
**Principle:** Reliability is measured, not assumed. Test until confident.

---

## Observed Reliability (Current Session)

| Test | Runs | Successes | Failures | Rate |
|------|------|-----------|----------|------|
| Video recording | 13 | 13 | 0 | 100% |
| Screenshot capture | 38 | 38 | 0 | 100% |
| Trace generation | 10 | 10 | 0 | 100% |
| API endpoint checks | 10 | 10 | 0 | 100% |
| Workflow execution | 13 | 13 | 0 | 100% |
| Container restart recovery | 2 | 2 | 0 | 100% |
| Frontend rendering | All | All | 0 | 100% |
| Console error-free | All | All | 0 | 100% |

**Session reliability: 100%** (single session, controlled environment)

---

## Reliability Test Suite

### Test 1: Repeated Execution (Stability)

```typescript
interface StabilityTest {
  name: "repeated-execution";
  iterations: 50;
  workflow: "deployment-verification";
  target: "http://localhost:3000";  // Self-verification
  
  pass_criteria: {
    success_rate: ">= 98%";        // Allow 1 transient failure in 50
    max_consecutive_failures: 2;
    execution_time_variance: "<= 20%";
    all_artifacts_produced: true;
  };
  
  measurements: [
    "execution_time_ms",
    "artifacts_produced",
    "retries_needed",
    "console_errors",
    "api_response_times",
  ];
}
```

### Test 2: Recovery Testing

```typescript
interface RecoveryTest {
  name: "recovery-validation";
  scenarios: [
    {
      name: "browser-crash-recovery";
      inject: "kill chromium process mid-execution";
      expected: "workflow recovers with fresh session";
      max_recovery_time_ms: 10000;
    },
    {
      name: "network-timeout-recovery";
      inject: "add 10s delay to target responses";
      expected: "adaptive timeout extends, workflow completes";
      max_recovery_time_ms: 30000;
    },
    {
      name: "api-error-recovery";
      inject: "target API returns 500 for first 2 requests";
      expected: "retry succeeds on 3rd attempt";
      max_recovery_time_ms: 15000;
    },
    {
      name: "container-restart-recovery";
      inject: "docker compose restart";
      expected: "system returns to healthy within 30s";
      max_recovery_time_ms: 30000;
    },
  ];
  
  pass_criteria: {
    all_scenarios_recovered: true;
    recovery_within_timeout: true;
    no_data_corruption: true;
    audit_trail_intact: true;
  };
}
```

### Test 3: Replay Consistency

```typescript
interface ReplayConsistencyTest {
  name: "replay-consistency";
  iterations: 10;
  
  procedure: [
    "Execute workflow and record",
    "Replay with recorded time source",
    "Compare outputs to original",
    "Verify determinism",
  ];
  
  pass_criteria: {
    identical_verdicts: "100%";
    identical_node_results: "100%";
    identical_governance_decisions: "100%";
    artifact_hash_match: ">= 95%";  // Allow minor rendering differences
  };
}
```

### Test 4: Environment Variability

```typescript
interface EnvironmentTest {
  name: "environment-variability";
  variations: [
    { name: "slow-network", config: "add 500ms latency" },
    { name: "low-memory", config: "limit container to 256MB" },
    { name: "high-cpu", config: "stress CPU to 80%" },
    { name: "dns-delay", config: "add 2s DNS resolution delay" },
    { name: "disk-pressure", config: "fill disk to 90%" },
  ];
  
  pass_criteria: {
    all_variations_complete: true;   // May be slower, but must complete
    no_crashes: true;
    graceful_degradation: true;      // Reduced score OK, crash not OK
  };
}
```

### Test 5: Session Resilience

```typescript
interface SessionResilienceTest {
  name: "session-resilience";
  duration_minutes: 60;
  workflow_interval_seconds: 300;   // Every 5 minutes
  
  measurements: [
    "memory_usage_over_time",
    "session_count_over_time",
    "response_time_trend",
    "error_rate_trend",
    "artifact_size_consistency",
  ];
  
  pass_criteria: {
    no_memory_leak: "memory growth < 10% over 1 hour";
    stable_performance: "p99 latency variance < 30%";
    no_session_accumulation: "active sessions <= 2 at any time";
    consistent_results: "all runs produce same verdict";
  };
}
```

### Test 6: Chaos Testing

```typescript
interface ChaosTest {
  name: "runtime-chaos";
  injections: [
    { type: "PROCESS_KILL", target: "chromium", frequency: "random 1/10 runs" },
    { type: "NETWORK_PARTITION", duration_ms: 5000, frequency: "random 1/20 runs" },
    { type: "MEMORY_PRESSURE", percent: 90, duration_ms: 10000 },
    { type: "DISK_FULL", duration_ms: 5000 },
    { type: "CPU_SPIKE", percent: 95, duration_ms: 3000 },
  ];
  
  pass_criteria: {
    system_never_corrupts_data: true;
    system_always_recovers_or_halts: true;
    no_silent_failures: true;        // Every failure is logged
    governance_never_bypassed: true;
    audit_trail_always_intact: true;
  };
}
```

---

## Reliability Metrics

```typescript
interface ReliabilityReport {
  period: string;                    // e.g., "last 24 hours"
  
  // Core metrics
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  recovered_executions: number;      // Failed then recovered
  
  // Rates
  success_rate: number;              // successful / total
  recovery_rate: number;             // recovered / (failed + recovered)
  availability: number;              // uptime / total_time
  
  // Performance
  mean_execution_time_ms: number;
  p50_execution_time_ms: number;
  p95_execution_time_ms: number;
  p99_execution_time_ms: number;
  
  // Stability
  mean_time_between_failures_ms: number;
  mean_time_to_recovery_ms: number;
  longest_failure_duration_ms: number;
  
  // Determinism
  replay_consistency_rate: number;
  determinism_score: number;         // 0-1
  
  // Verdict
  production_ready: boolean;
  confidence_level: "LOW" | "MEDIUM" | "HIGH" | "VERY_HIGH";
}
```

---

## Confidence Levels

| Level | Criteria |
|-------|----------|
| LOW | < 50 runs, or success rate < 95% |
| MEDIUM | 50-200 runs, success rate >= 95%, recovery rate >= 80% |
| HIGH | 200-1000 runs, success rate >= 99%, recovery rate >= 90% |
| VERY_HIGH | 1000+ runs, success rate >= 99.9%, recovery rate >= 95% |

**Current level: MEDIUM** (based on ~100 operations at 100% success, but single session)

To reach HIGH: need sustained execution over multiple days with varied conditions.

---

## Test Execution Schedule

| Test | Frequency | Duration | Automated |
|------|-----------|----------|-----------|
| Stability (50 runs) | Daily | ~10 min | Yes |
| Recovery (4 scenarios) | Daily | ~5 min | Yes |
| Replay consistency (10 runs) | Daily | ~5 min | Yes |
| Environment variability | Weekly | ~30 min | Yes |
| Session resilience | Weekly | 1 hour | Yes |
| Chaos testing | Weekly | ~15 min | Yes |

---

## Mapping to Current Implementation

| Concept | Existing | Gap |
|---------|----------|-----|
| Execution tracking | `WorkflowExecution` records | ✓ Working |
| Success/failure recording | `WorkflowExecutionState` | ✓ Working |
| Container restart | Docker healthcheck + restart | ✓ Validated |
| API health checks | `/api/health` endpoint | ✓ Working |
| Telemetry counters | `ExecutionTelemetryCollector` | ✓ Working |
| Replay recording | `ReplayRecorder` | ✓ Working |
| Automated test runner | `scripts/record-final.js` | Extend for reliability |
| Chaos injection | Not implemented | New |
| Long-running stability | Not tested | New |
| Confidence scoring | Not implemented | New |
