# Self-Healing Execution

**Module:** `nexusos.runtime.self_healing`  
**Principle:** Recover autonomously. Record every remediation. Never hide a failure.

---

## Recovery Architecture

```
Failure Detected
    │
    ├── 1. Classify (failure-intelligence)
    │       → Origin, Severity, Recoverability
    │
    ├── 2. Select Strategy
    │       → Based on classification + history
    │
    ├── 3. Validate with Governance
    │       → Recovery action must be permitted
    │
    ├── 4. Execute Recovery
    │       → Apply strategy, record every step
    │
    ├── 5. Verify Recovery
    │       → Confirm system returned to healthy state
    │
    └── 6. Record
            → Audit trail, telemetry, replay record
```

---

## Recovery Strategies

### 1. Automatic Retry

```typescript
interface AutoRetry {
  trigger: "TRANSIENT failure";
  behavior: {
    max_attempts: 3;
    backoff: "EXPONENTIAL";
    base_delay_ms: 1000;
    max_delay_ms: 30000;
    jitter: true;
  };
  success_criteria: "Operation completes without error";
  rollback: "None (idempotent operations only)";
}
```

**Applied to:** Network timeouts, DNS blips, rate limits, transient API errors.

### 2. Adaptive Timeout Recovery

```typescript
interface AdaptiveTimeout {
  trigger: "Operation exceeds timeout threshold";
  behavior: {
    initial_timeout_ms: 30000;
    extension_factor: 1.5;          // Extend by 50% on timeout
    max_timeout_ms: 120000;
    measure_actual_duration: true;   // Learn real timing
    adjust_baseline: true;           // Update expectations
  };
  success_criteria: "Operation completes within extended timeout";
  rollback: "Abort and report timeout with actual duration";
}
```

**Applied to:** Slow page loads, large API responses, video encoding delays.

### 3. Selector Healing

```typescript
interface SelectorHealing {
  trigger: "Element not found with primary selector";
  behavior: {
    strategies: [
      "ROLE_BASED",      // getByRole('button', {name: 'Submit'})
      "TEXT_CONTENT",    // getByText('Submit')
      "TEST_ID",         // getByTestId('submit-btn')
      "ARIA_LABEL",      // [aria-label="Submit"]
      "PARTIAL_MATCH",   // Contains text
      "STRUCTURAL",      // nth-child, sibling relationships
    ];
    max_attempts: 3;     // Try up to 3 alternative strategies
    record_healing: true; // Log which strategy worked
    update_primary: false; // Don't auto-update (human review)
  };
  success_criteria: "Element found and interactable";
  rollback: "Report element not found with all strategies tried";
}
```

**Applied to:** Layout changes, CSS class renames, DOM restructuring.

### 4. Session Restoration

```typescript
interface SessionRestoration {
  trigger: "Session corruption detected";
  behavior: {
    steps: [
      "CLOSE_CONTEXT",       // Close corrupted browser context
      "CREATE_FRESH",        // New context with same config
      "RESTORE_COOKIES",     // If session cookies were captured
      "NAVIGATE_TO_LAST",    // Return to last known good URL
      "VERIFY_STATE",        // Confirm page renders correctly
    ];
    preserve_artifacts: true; // Keep screenshots/video from before corruption
    checkpoint_before: true;  // Save state before restoration attempt
  };
  success_criteria: "New session reaches expected page state";
  rollback: "Abort workflow, report session unrecoverable";
}
```

**Applied to:** Browser crashes, memory pressure, context corruption.

### 5. Browser Recovery

```typescript
interface BrowserRecovery {
  trigger: "Browser process unresponsive or crashed";
  behavior: {
    steps: [
      "KILL_PROCESS",        // Force-kill hung browser
      "WAIT_CLEANUP",        // Allow OS to release resources (2s)
      "LAUNCH_NEW",          // Start fresh Chromium instance
      "VERIFY_LAUNCH",       // Confirm browser responds
      "RESTORE_SESSION",     // Navigate to workflow position
    ];
    max_recovery_attempts: 2;
    cooldown_between_ms: 5000;
  };
  success_criteria: "New browser instance operational";
  rollback: "Abort workflow, report browser unrecoverable";
}
```

### 6. Execution Rollback

```typescript
interface ExecutionRollback {
  trigger: "Workflow step fails after producing side effects";
  behavior: {
    checkpoint_required: true;       // Must have checkpoint to rollback
    steps: [
      "IDENTIFY_CHECKPOINT",         // Find last valid checkpoint
      "RESTORE_STATE",               // Reset to checkpoint state
      "DISCARD_ARTIFACTS",           // Remove artifacts after checkpoint
      "RESET_TELEMETRY",             // Clear metrics after checkpoint
      "RESUME_FROM_CHECKPOINT",      // Continue execution
    ];
  };
  success_criteria: "Execution resumes from checkpoint successfully";
  rollback: "Abort workflow, report partial completion";
}
```

### 7. Runtime Stabilization

```typescript
interface RuntimeStabilization {
  trigger: "Multiple subsystems degraded simultaneously";
  behavior: {
    steps: [
      "PAUSE_NEW_WORK",             // Stop accepting new workflows
      "DRAIN_ACTIVE",               // Let active workflows complete/timeout
      "HEALTH_DIAGNOSTIC",          // Full system diagnostic
      "RESTART_UNHEALTHY",          // Restart degraded components
      "VERIFY_HEALTH",              // Confirm all components healthy
      "RESUME_WORK",                // Accept new workflows
    ];
    max_stabilization_time_ms: 60000;
    governance_required: true;       // Must be approved
  };
  success_criteria: "All components return to HEALTHY";
  rollback: "HALT system, alert operator";
}
```

---

## Deterministic Recovery Guarantees

| Guarantee | Implementation |
|-----------|---------------|
| Same failure → same recovery strategy | Classification is deterministic |
| Recovery actions are audited | Every action passes governance + audit |
| Recovery is replayable | All inputs/decisions recorded |
| Recovery doesn't hide failures | Original failure always in audit trail |
| Recovery doesn't corrupt state | Checkpoint before any state modification |
| Recovery has bounded time | Every strategy has max timeout |
| Recovery can be disabled | Governance can deny recovery actions |

---

## Traceable Remediation

Every recovery produces a remediation record:

```typescript
interface RemediationRecord {
  id: string;
  timestamp: string;
  
  // What failed
  failure: {
    classification: FailureClassification;
    error_message: string;
    stack_trace: string | null;
    context: Record<string, unknown>;
  };
  
  // What was tried
  strategy: string;
  attempts: {
    attempt_number: number;
    action: string;
    timestamp: string;
    result: "SUCCESS" | "FAILED" | "TIMEOUT";
    duration_ms: number;
  }[];
  
  // Outcome
  outcome: "RECOVERED" | "ESCALATED" | "ABORTED";
  recovery_duration_ms: number;
  
  // Governance
  governance_decision_id: string;
  audit_record_id: string;
  
  // Replay
  replay_safe: boolean;            // Can this recovery be replayed?
  checkpoint_id: string | null;    // Checkpoint used for rollback
}
```

---

## Replay-Safe Corrections

Recovery actions must not break replay:

| Recovery Action | Replay-Safe? | Reason |
|----------------|-------------|--------|
| Retry same operation | ✅ Yes | Idempotent, same inputs |
| Extend timeout | ✅ Yes | Same operation, more time |
| Alternative selector | ⚠️ Conditional | Record which selector worked |
| Fresh session | ✅ Yes | Deterministic from same starting point |
| Browser restart | ✅ Yes | Clean state, deterministic |
| Rollback to checkpoint | ✅ Yes | Checkpoint is recorded state |
| Skip non-critical step | ⚠️ Conditional | Must record skip decision |
| Modify request params | ❌ No | Changes execution semantics |

For conditional cases: the recovery decision is recorded in the replay manifest so replay can follow the same path.

---

## Mapping to Current Implementation

| Concept | Existing | Gap |
|---------|----------|-----|
| Health monitoring | `RuntimeHealthMonitor` | Add failure classification |
| Component restart | Docker `restart: unless-stopped` | Add in-process recovery |
| Browser sessions | `BrowserRuntime` | Add corruption detection + restoration |
| Workflow state | `WorkflowExecutionState` | Add RECOVERING state |
| Governance validation | `GovernanceEngine` | Add recovery-specific policies |
| Audit trail | `AuditLogger` | Add remediation records |
| Checkpoints | Not implemented | New: state snapshot system |
| Selector strategies | Not implemented | New: multi-strategy element finding |
