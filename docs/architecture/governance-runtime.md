# Governance Runtime

**Module:** `nexusos.governance`  
**Status:** Architecture Specification  
**Principle:** All system behavior is governed. No uncontrolled execution.

---

## Overview

The Governance Runtime is the foundational layer of NexusOS. It is not optional, not advisory, and not layered on top — it is the substrate through which all execution flows. Every operation must be validated before execution. If governance cannot be applied, the operation does not proceed.

---

## Policy Engine

```
┌─────────────────────────────────────────────────────────┐
│                    PolicyEngine                           │
├─────────────────────────────────────────────────────────┤
│  policies: Policy[]                                      │
│  evaluation_mode: DENY_BY_DEFAULT | ALLOW_BY_DEFAULT     │
│  audit_logger: AuditLogger                               │
│  decision_cache: LRU<string, Decision>                   │
│                                                         │
│  validate(action, resource, context) → Decision          │
│  register_policy(policy) → void                          │
│  evaluate_all(action) → Decision[]                       │
└─────────────────────────────────────────────────────────┘
```

### Policy Structure

```
┌─────────────────────────────────────────────────────────┐
│                      Policy                              │
├─────────────────────────────────────────────────────────┤
│  id: string                                              │
│  name: string                                            │
│  priority: number (higher = evaluated first)             │
│  active: boolean                                         │
│  permissions: Permission[]                               │
│  conditions: Condition[] (contextual constraints)        │
│  scope: PolicyScope (GLOBAL | WORKFLOW | NODE | AGENT)    │
│  expires_at: ISO string (optional)                       │
└─────────────────────────────────────────────────────────┘
```

### Decision Model

```
┌─────────────────────────────────────────────────────────┐
│                     Decision                             │
├─────────────────────────────────────────────────────────┤
│  permitted: boolean                                      │
│  action: string                                          │
│  resource: string                                        │
│  reason: string                                          │
│  policy_id: string                                       │
│  timestamp: ISO string                                   │
│  audit_record_id: string                                 │
│  conditions_evaluated: ConditionResult[]                  │
└─────────────────────────────────────────────────────────┘
```

---

## Governance Evaluation Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Request  │───→│ Validate │───→│ Evaluate │───→│ Decide   │
│          │    │          │    │          │    │          │
│ action   │    │ schema   │    │ policies │    │ permit/  │
│ resource │    │ context  │    │ priority │    │ deny     │
│ actor    │    │ complete │    │ order    │    │          │
└──────────┘    └──────────┘    └──────────┘    └────┬─────┘
                                                      │
                                                      ▼
                                                ┌──────────┐
                                                │  Audit   │
                                                │          │
                                                │ record   │
                                                │ checksum │
                                                │ store    │
                                                └──────────┘
```

---

## Runtime Trust Zones

```
┌─────────────────────────────────────────────────────────────┐
│                        ZONE 0: KERNEL                         │
│  Governance engine, audit logger, policy store               │
│  Trust: Absolute — cannot be overridden                      │
├─────────────────────────────────────────────────────────────┤
│                     ZONE 1: ORCHESTRATION                     │
│  Workflow engine, execution graph, scheduler                 │
│  Trust: High — governed by Zone 0 policies                   │
├─────────────────────────────────────────────────────────────┤
│                      ZONE 2: EXECUTION                        │
│  Browser runtime, terminal runtime, skill runtime            │
│  Trust: Medium — sandboxed, validated per-operation          │
├─────────────────────────────────────────────────────────────┤
│                      ZONE 3: EXTERNAL                         │
│  MCP tools, external APIs, user inputs                       │
│  Trust: None — all inputs validated, all outputs verified    │
└─────────────────────────────────────────────────────────────┘
```

---

## Capability Boundaries

Each runtime component has declared capabilities:

```
┌────────────────────────────────────────────────────────┐
│  BrowserRuntime Capabilities                            │
├────────────────────────────────────────────────────────┤
│  ALLOWED: navigate, click, type, screenshot, close      │
│  BLOCKED: file:// URLs, javascript: URLs                │
│  RATE_LIMITED: navigate (10/min), screenshot (30/min)   │
│  REQUIRES_APPROVAL: download, upload, cookie_access     │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  TerminalRuntime Capabilities                           │
├────────────────────────────────────────────────────────┤
│  ALLOWED: read commands, safe utilities                  │
│  BLOCKED: shutdown, reboot, mkfs, rm -rf /              │
│  TIMEOUT: 30s default, 300s maximum                     │
│  SANDBOX: working_dir restricted, no PATH modification  │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  WorkflowEngine Capabilities                            │
├────────────────────────────────────────────────────────┤
│  ALLOWED: BROWSER, TERMINAL, CUSTOM, SKILL step types   │
│  MAX_STEPS: 100 per workflow                            │
│  MAX_DEPTH: 10 dependency levels                        │
│  REQUIRES_APPROVAL: workflows with >20 steps            │
└────────────────────────────────────────────────────────┘
```

---

## MCP Governance

MCP tool invocations are governed:

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ MCP Call │───→│Governance│───→│ Validate │───→│ Execute  │
│          │    │  Gate    │    │          │    │          │
│ tool     │    │ check    │    │ params   │    │ if       │
│ params   │    │ policy   │    │ bounds   │    │ permitted│
│ context  │    │ scope    │    │ safety   │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## Governance Gates in Execution Graphs

```json
{
  "id": "gov-gate-001",
  "type": "GOVERNANCE",
  "config": {
    "required_policy": "production-deploy",
    "approval_mode": "AUTOMATIC | MANUAL | CONDITIONAL",
    "timeout_ms": 30000,
    "fallback": "DENY"
  }
}
```

Governance gates are execution graph nodes that block progression until policy approval is confirmed.

---

## Audit Integrity

Every governance decision produces a tamper-evident audit record:

```
record_id = SHA-256(action + actor + timestamp + sequence)
checksum = SHA-256(record_id + timestamp + action + actor + resource + outcome + sequence)
```

Audit records are append-only. Deletion is not permitted. Verification is performed by recomputing checksums.

---

## Integration with Existing Code

| Architecture Component | Current Implementation |
|----------------------|----------------------|
| PolicyEngine | `GovernanceEngine` (backend/governance/engine.py) |
| Decision | `ValidationResult` (backend/governance/models.py) |
| AuditLogger | `AuditLogger` (backend/governance/audit.py) |
| Capability validation | `ExecutionGovernanceValidator` (backend/governance/execution.py) |
| Deny-by-default | Implemented in `validate_action()` |
| Checksum integrity | Implemented in `AuditLogger.log()` |

Evolution extends with: trust zones, capability boundaries, MCP governance, conditional policies, and governance gates in execution graphs.
