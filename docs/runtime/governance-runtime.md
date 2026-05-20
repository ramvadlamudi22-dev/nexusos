# Governance Runtime

**Module:** `nexusos.runtime.governance`  
**Principle:** If governance cannot validate an operation, that operation does not execute.

---

## Execution Policies

Policies define what the runtime is allowed to do:

```typescript
interface ExecutionPolicy {
  id: string;
  name: string;
  scope: PolicyScope;
  rules: PolicyRule[];
  active: boolean;
  priority: number;                // Higher = evaluated first
}

interface PolicyRule {
  action_pattern: string;          // Glob: "browser.*", "terminal.execute"
  resource_pattern: string;        // Glob: "https://*.example.com/*"
  effect: "ALLOW" | "DENY" | "REQUIRE_APPROVAL";
  conditions: RuleCondition[];
  rate_limit: RateLimit | null;
}

interface RuleCondition {
  type: "TIME_WINDOW" | "RATE" | "CONTEXT" | "TRUST_ZONE";
  params: Record<string, unknown>;
}
```

### Default Policies

| Policy | Scope | Effect | Purpose |
|--------|-------|--------|---------|
| `allow-verification` | WORKFLOW | ALLOW browser.navigate, browser.screenshot, api.check | Core verification operations |
| `block-dangerous-urls` | GLOBAL | DENY browser.navigate to file://, javascript: | Safety |
| `block-dangerous-commands` | GLOBAL | DENY terminal.execute shutdown, reboot, rm -rf / | Safety |
| `rate-limit-navigation` | GLOBAL | ALLOW browser.navigate (max 30/min) | Stability |
| `require-approval-destructive` | GLOBAL | REQUIRE_APPROVAL for terminal.execute with write ops | Safety |

---

## Runtime Safety Gates

Safety gates are checkpoints that block execution until validated:

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Operation│───→│  Safety  │───→│ Execute  │
│ Request  │    │   Gate   │    │          │
└──────────┘    └────┬─────┘    └──────────┘
                     │
                     │ Checks:
                     ├── 1. Action permitted by policy?
                     ├── 2. Resource within allowed scope?
                     ├── 3. Rate limit not exceeded?
                     ├── 4. Trust zone allows this?
                     ├── 5. No active safety hold?
                     │
                     ├── ALL PASS → Execute
                     └── ANY FAIL → Deny + Audit
```

### Gate Types

| Gate | Checks | Applied To |
|------|--------|-----------|
| URL Gate | Blocked schemes, allowed domains | Browser navigation |
| Command Gate | Blocked commands, allowed patterns | Terminal execution |
| Rate Gate | Operations per time window | All operations |
| Scope Gate | Resource within declared boundary | All operations |
| Trust Gate | Caller's trust zone permits action | Cross-zone calls |
| Health Gate | System healthy enough to proceed | New workflow starts |

---

## Action Validation

Every action is validated before execution:

```python
def validate_action(action: str, resource: str, context: dict) -> Decision:
    """
    Validate an action against all active policies.
    
    Returns PERMIT only if:
    1. At least one policy explicitly allows the action
    2. No policy explicitly denies the action
    3. All conditions are met
    4. Rate limits are not exceeded
    
    Default: DENY (if no policy matches)
    """
```

### Validation Examples

```
Action: browser.navigate
Resource: https://app.example.com/dashboard
Context: {workflow: "deploy-verify", node: "check-dashboard"}
→ Decision: PERMIT (allowed by allow-verification policy)

Action: browser.navigate
Resource: file:///etc/passwd
Context: {workflow: "deploy-verify", node: "check-files"}
→ Decision: DENY (blocked by block-dangerous-urls policy)

Action: terminal.execute
Resource: "rm -rf /"
Context: {workflow: "cleanup", node: "remove-temp"}
→ Decision: DENY (blocked by block-dangerous-commands policy)

Action: browser.navigate
Resource: https://app.example.com/page-31
Context: {workflow: "deploy-verify", rate: 31/min}
→ Decision: DENY (rate limit exceeded: 30/min max)
```

---

## Policy-Aware Workflows

Workflows declare their governance requirements:

```typescript
interface GovernedWorkflow {
  definition: ExecutionGraph;
  
  // Governance declaration
  governance: {
    required_policies: string[];     // Policies that must be active
    required_permissions: string[];  // Actions the workflow needs
    trust_zone: TrustZone;          // Zone the workflow runs in
    max_operations: number;          // Self-imposed limit
    timeout_ms: number;              // Self-imposed deadline
  };
  
  // Pre-validation
  // Before execution starts, verify all required permissions are available
  // If any required permission would be denied, abort before starting
}
```

---

## Deterministic Enforcement

Governance decisions are deterministic:
- Same policy set + same action + same context → same decision
- Decisions are cached (invalidated on policy change)
- Policy evaluation order is fixed (by priority, then by ID)
- No randomness in evaluation

This means governance decisions replay identically.

---

## Execution Auditability

Every governance decision produces an immutable audit record:

```typescript
interface GovernanceAuditRecord {
  id: string;                      // SHA-256(content + sequence)
  sequence: number;                // Monotonic, gap-free
  timestamp: string;
  
  // What was requested
  action: string;
  resource: string;
  actor: string;                   // Component/workflow that requested
  context: Record<string, string>;
  
  // What was decided
  decision: "PERMIT" | "DENY" | "PENDING";
  reason: string;
  policy_id: string;
  rule_index: number;
  
  // Integrity
  checksum: string;                // SHA-256 for tamper detection
  previous_checksum: string;       // Hash chain to previous record
}
```

### Hash Chain

```
Record 1: checksum = SHA-256(content_1)
Record 2: checksum = SHA-256(content_2), previous = checksum_1
Record 3: checksum = SHA-256(content_3), previous = checksum_2
...
```

Any modification to a historical record breaks the chain → tampering detected.

---

## Operational Guardrails

Hard limits that cannot be overridden by policy:

| Guardrail | Limit | Rationale |
|-----------|-------|-----------|
| Max workflow duration | 10 minutes | Prevent runaway execution |
| Max concurrent workflows | 10 | Resource protection |
| Max browser sessions | 5 | Memory protection |
| Max terminal commands/min | 60 | Rate protection |
| Max artifact size | 100 MB | Storage protection |
| Max retry attempts | 10 | Prevent infinite loops |
| Max checkpoint size | 50 MB | Storage protection |
| Governance evaluation timeout | 100ms | Performance protection |

These are system-level constraints, not policy-level. They exist to protect the runtime itself.

---

## Mapping to Current Implementation

| Concept | Existing | Gap |
|---------|----------|-----|
| Policy evaluation | `GovernanceEngine.validate_action()` | Add conditions, rate limits |
| Deny-by-default | ✓ Implemented | Working |
| URL blocking | `ExecutionGovernanceValidator.validate_browser_action()` | ✓ Working |
| Command blocking | `validate_terminal_command()` | ✓ Working |
| Workflow validation | `validate_workflow_execution()` | Add pre-validation |
| Audit logging | `AuditLogger` with checksums | Add hash chain |
| Policy store | In-memory dict | Add priority, conditions |
| Rate limiting | Not implemented | New |
| Trust zones | Not implemented | New |
| Guardrails | Partial (MAX_WORKFLOW_STEPS=100) | Extend |
