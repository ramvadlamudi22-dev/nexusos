# Governance Engine

**Module:** `nexusos.runtime.governance`  
**Version:** 2.0  
**Principle:** Governance is the foundation, not a layer. No operation proceeds without validation.

---

## Design Intent

The Governance Engine is the substrate of NexusOS. Every operation — browser action, terminal command, workflow step, agent message, recovery action — must pass through governance before execution. The engine evaluates policies contextually, enforces capability boundaries, maintains trust zones, and produces tamper-evident audit records for every decision.

---

## Policy Engine Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Policy Engine                            │
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  │
│  │ Policy Store  │  │  Evaluator    │  │ Decision Cache│  │
│  │               │  │               │  │               │  │
│  │ Versioned     │  │ Priority-     │  │ LRU with TTL  │  │
│  │ Scoped        │  │ ordered       │  │ Invalidation  │  │
│  │ Conditional   │  │ Short-circuit │  │ on policy Δ   │  │
│  └───────────────┘  └───────────────┘  └───────────────┘  │
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  │
│  │ Audit Logger  │  │ Trust Zones   │  │ Capability    │  │
│  │               │  │               │  │ Registry      │  │
│  │ Append-only   │  │ Zone 0-3      │  │               │  │
│  │ Checksummed   │  │ Hierarchical  │  │ Per-component │  │
│  │ Immutable     │  │ Inherited     │  │ Declared      │  │
│  └───────────────┘  └───────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Policy Model

```typescript
interface Policy {
  id: string;
  name: string;
  version: string;                   // Semantic version
  priority: number;                  // Higher = evaluated first
  active: boolean;
  scope: PolicyScope;
  permissions: Permission[];
  conditions: PolicyCondition[];     // Contextual constraints
  expires_at: string | null;
  created_at: string;
  checksum: string;                  // Policy integrity
}

enum PolicyScope {
  GLOBAL     = "GLOBAL",      // Applies to all operations
  WORKFLOW   = "WORKFLOW",    // Applies within workflow execution
  NODE       = "NODE",        // Applies to specific node types
  AGENT      = "AGENT",       // Applies to specific agent
  RUNTIME    = "RUNTIME",     // Applies to specific runtime
  MCP        = "MCP",         // Applies to MCP tool calls
}

interface Permission {
  action: string;                    // Action pattern (supports wildcards)
  resource: string;                  // Resource pattern
  level: "ALLOW" | "DENY" | "REQUIRE_APPROVAL";
  conditions: PermissionCondition[]; // Additional constraints
}

interface PolicyCondition {
  type: "TIME_WINDOW" | "RATE_LIMIT" | "CONTEXT_MATCH" | 
        "TRUST_ZONE" | "EXECUTION_STATE";
  params: Record<string, unknown>;
}
```

---

## Evaluation Algorithm

```python
def evaluate(action: str, resource: str, context: EvalContext) -> Decision:
    # 1. Check decision cache
    cache_key = f"{action}:{resource}:{context.hash()}"
    if cached := cache.get(cache_key):
        return cached
    
    # 2. Evaluate policies in priority order (highest first)
    for policy in sorted(active_policies, key=lambda p: -p.priority):
        # Skip if policy scope doesn't match context
        if not scope_matches(policy.scope, context):
            continue
        
        # Skip if policy conditions not met
        if not conditions_met(policy.conditions, context):
            continue
        
        # Evaluate permissions
        for permission in policy.permissions:
            if action_matches(permission.action, action) and \
               resource_matches(permission.resource, resource):
                
                # Check permission-level conditions
                if conditions_met(permission.conditions, context):
                    decision = Decision(
                        permitted=(permission.level == "ALLOW"),
                        requires_approval=(permission.level == "REQUIRE_APPROVAL"),
                        action=action,
                        resource=resource,
                        reason=f"{'Allowed' if permission.level == 'ALLOW' else 'Denied'} by {policy.name}",
                        policy_id=policy.id,
                    )
                    
                    # Audit every decision
                    audit_logger.record(decision)
                    
                    # Cache the decision
                    cache.set(cache_key, decision, ttl=policy_cache_ttl)
                    
                    return decision
    
    # 3. Default deny (no policy explicitly allows)
    decision = Decision(
        permitted=False,
        action=action,
        resource=resource,
        reason="No policy permits this action (default deny)",
    )
    audit_logger.record(decision)
    return decision
```

---

## Trust Zones

```
┌─────────────────────────────────────────────────────────────┐
│  ZONE 0: GOVERNANCE KERNEL                                   │
│  Components: PolicyEngine, AuditLogger, TrustZoneManager     │
│  Trust: Absolute — self-governing, cannot be overridden      │
│  Permissions: All (unrestricted within zone)                 │
│  Isolation: Cannot be modified by other zones                │
├─────────────────────────────────────────────────────────────┤
│  ZONE 1: ORCHESTRATION                                       │
│  Components: ExecutionGraphEngine, Scheduler, AgentCoordinator│
│  Trust: High — governed by Zone 0                            │
│  Permissions: Create/execute workflows, coordinate agents    │
│  Constraints: Cannot modify governance policies              │
├─────────────────────────────────────────────────────────────┤
│  ZONE 2: EXECUTION                                           │
│  Components: BrowserRuntime, TerminalRuntime, SkillRuntime   │
│  Trust: Medium — sandboxed, per-operation validation         │
│  Permissions: Execute within declared capabilities           │
│  Constraints: Cannot access other sessions, rate-limited     │
├─────────────────────────────────────────────────────────────┤
│  ZONE 3: EXTERNAL                                            │
│  Components: MCP tools, external APIs, user inputs           │
│  Trust: None — all inputs validated, outputs verified         │
│  Permissions: Only what's explicitly granted per-call        │
│  Constraints: Sandboxed, timeout-enforced, output-validated  │
└─────────────────────────────────────────────────────────────┘
```

### Zone Inheritance

Policies defined at a higher zone apply to all lower zones unless explicitly overridden. A Zone 2 component cannot grant itself Zone 1 permissions.

---

## Capability Boundaries

```typescript
interface CapabilityDeclaration {
  component: string;
  zone: TrustZone;
  capabilities: {
    allowed: string[];             // Permitted operations
    blocked: string[];             // Explicitly forbidden
    rate_limited: RateLimit[];     // Throttled operations
    requires_approval: string[];   // Need explicit governance gate
  };
  resource_limits: {
    max_concurrent_operations: number;
    max_memory_bytes: number;
    max_execution_time_ms: number;
    max_network_requests_per_minute: number;
  };
}
```

### Runtime Capability Declarations

| Runtime | Allowed | Blocked | Rate Limited |
|---------|---------|---------|-------------|
| Browser | navigate, click, type, screenshot | file://, javascript: | navigate: 10/min |
| Terminal | safe commands, read operations | shutdown, reboot, rm -rf / | commands: 30/min |
| Workflow | create, execute, checkpoint | >100 steps, cyclic graphs | executions: 60/min |
| Skill | registered skills only | unregistered invocations | invocations: 100/min |

---

## MCP Governance Layer

```typescript
interface MCPGovernanceConfig {
  tool_policies: MCPToolPolicy[];
  default_action: "DENY" | "ALLOW" | "REQUIRE_APPROVAL";
  audit_all_calls: boolean;
  parameter_validation: boolean;
  output_verification: boolean;
}

interface MCPToolPolicy {
  tool_pattern: string;            // Regex matching tool names
  permission: "ALLOW" | "DENY" | "REQUIRE_APPROVAL";
  parameter_constraints: ParameterConstraint[];
  rate_limit: RateLimit | null;
  sandbox: boolean;
  timeout_ms: number;
}
```

### MCP Call Flow

```
MCP Tool Call Request
    │
    ├── 1. Tool name validation (against policy patterns)
    ├── 2. Parameter validation (against constraints)
    ├── 3. Rate limit check
    ├── 4. Trust zone verification (caller's zone)
    ├── 5. Governance decision (permit/deny/approve)
    ├── 6. Audit record creation
    │
    ├── [PERMITTED] → Execute tool → Verify output → Return
    └── [DENIED] → Return denial reason → Log → Alert if suspicious
```

---

## Action Mediation

The governance engine mediates all actions through a unified interface:

```typescript
interface GovernanceMediator {
  // Synchronous validation (fast path)
  validate(request: ActionRequest): Decision;
  
  // Asynchronous approval (for REQUIRE_APPROVAL)
  requestApproval(request: ActionRequest): Promise<Decision>;
  
  // Batch validation (for workflow pre-validation)
  validateBatch(requests: ActionRequest[]): Decision[];
  
  // Policy management
  registerPolicy(policy: Policy): void;
  deactivatePolicy(policyId: string): void;
  
  // Introspection
  explainDecision(decisionId: string): DecisionExplanation;
  simulateAction(request: ActionRequest): Decision;  // Dry-run
}
```

---

## Audit Integrity

```typescript
interface AuditRecord {
  id: string;                      // SHA-256(content + sequence)
  sequence: number;                // Monotonic, gap-free
  timestamp: string;
  action: string;
  actor: string;                   // Component/agent that requested
  resource: string;
  outcome: "PERMITTED" | "DENIED" | "PENDING_APPROVAL";
  policy_id: string;
  reason: string;
  context_hash: string;            // Hash of evaluation context
  checksum: string;                // SHA-256 for integrity
  previous_checksum: string;       // Chain to previous record
}
```

The `previous_checksum` field creates a hash chain — any modification to a historical record breaks the chain, making tampering detectable.

---

## Mapping to Current Implementation

| New Concept | Existing Code | Gap |
|-------------|--------------|-----|
| Policy evaluation | `GovernanceEngine.validate_action()` | Add conditions, scopes, priority |
| Deny-by-default | Already implemented | ✓ |
| Audit logging | `AuditLogger` with checksums | Add hash chain (previous_checksum) |
| Browser governance | `ExecutionGovernanceValidator.validate_browser_action()` | Add rate limits |
| Terminal governance | `validate_terminal_command()` | Add capability boundaries |
| Workflow governance | `validate_workflow_execution()` | Add step-level validation |
| Policy store | In-memory dict | Add versioning, expiration |
| Trust zones | Not implemented | New: hierarchical zone model |
| MCP governance | Not implemented | New: tool-level policy engine |
| Decision cache | Not implemented | New: LRU with TTL |
