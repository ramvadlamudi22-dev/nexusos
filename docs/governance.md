# Governance Enforcement Reference

NexusOS enforces governance on every runtime action. This document covers how governance policies work, how to configure them, and how to use the audit trail.

## Philosophy: Deny-by-Default

The governance engine follows a **deny-by-default** model. If no active policy explicitly permits an action, the action is denied. This means:

1. A freshly started system with no policies blocks all mutating actions.
2. Policies must explicitly grant `ALLOW` for actions to proceed.
3. Any policy with a `DENY` permission takes precedence over an `ALLOW` from another policy.
4. Governance is structural, not advisory. It cannot be bypassed by runtime code.

The enforcement logic lives in `backend/governance/engine.py` in the `validate_action` method.

## Policy Model

Governance is built on three models defined in `backend/governance/models.py`:

### PermissionLevel

An enum with three values:

| Level   | Meaning                                          |
|---------|--------------------------------------------------|
| `ALLOW` | The action is explicitly permitted               |
| `DENY`  | The action is explicitly blocked                 |
| `AUDIT` | The action proceeds but is flagged for review    |

### Permission

A single permission entry within a policy:

```python
class Permission(BaseModel):
    action: str                           # e.g. "runtime.register", "*"
    level: PermissionLevel = PermissionLevel.DENY
    resource: str = "*"                   # e.g. "browser", "*"
```

- `action` is matched against the action string passed to `validate_action`.
- `resource` further scopes the permission. `"*"` matches any resource.

### Policy

A named collection of permissions:

```python
class Policy(BaseModel):
    id: str
    name: str
    description: str = ""
    permissions: List[Permission] = []
    active: bool = True
```

- Inactive policies (`active=False`) are skipped during evaluation.
- Policies are stored in-memory by the `GovernanceEngine`.

### ValidationResult

Returned by every governance check:

```python
class ValidationResult(BaseModel):
    permitted: bool
    action: str
    reason: str = ""
    policy_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
```

## How Policy Evaluation Works

When `GovernanceEngine.validate_action(action, resource)` is called:

1. Iterate over all registered policies in insertion order.
2. Skip policies with `active=False`.
3. For each permission in the policy:
   - If the permission's `action` matches (exact match or `"*"`) AND the `resource` matches (exact match or `"*"`):
     - If `level == DENY`: immediately return denied with the policy name.
     - If `level == ALLOW`: immediately return permitted with the policy name.
4. If no permission matched across all policies, return denied with reason "No policy permits this action (default deny)".

This means the first matching permission wins. Order policies carefully.

## Registering Custom Policies

Policies are registered via code during application startup. There is no HTTP endpoint for policy registration -- policies are defined in `backend/main.py` and loaded when the app starts.

### Via Code (in backend/main.py)

```python
from backend.governance.models import Permission, PermissionLevel, Policy

policy = Policy(
    id="my-custom-policy",
    name="My Custom Policy",
    permissions=[
        Permission(action="runtime.register", level=PermissionLevel.ALLOW),
        Permission(action="terminal_command", level=PermissionLevel.DENY, resource="production"),
    ],
    active=True,
)
governance_engine.register_policy(policy)
```

Use `governance_engine.remove_policy(policy_id)` to remove a policy at runtime.

### Default Development Policy

The default configuration in `backend/main.py` registers a permissive "Default Allow All" policy:

```python
Policy(
    id="default-allow-all",
    name="Default Allow All",
    description="Default permissive policy for development. Must be replaced in production.",
    permissions=[
        Permission(action="*", level=PermissionLevel.ALLOW, resource="*")
    ],
    active=True,
)
```

Replace this with restrictive policies for production deployments.

## Execution Governance Validator

The `ExecutionGovernanceValidator` in `backend/governance/execution.py` provides specialized validation for runtime actions beyond basic policy checks. It enforces safety constraints directly:

### Browser Actions

- Blocks dangerous URL schemes: `file://`, `javascript:`
- All other URLs are permitted (subject to policy engine)

### Terminal Commands

- Blocks destructive commands: `rm -rf /`, `shutdown`, `reboot`, `mkfs`
- Validates against the blocklist before execution proceeds

### Workflow Execution

- Maximum step count: 100 steps per workflow
- Valid step types: `BROWSER`, `TERMINAL`, `SKILL`, `CUSTOM`
- Invalid step types are rejected

### Skill Invocations

- Validates that the skill ID exists in the skill registry
- Unregistered skills are denied

The validator is called on every execution endpoint in `backend/api/execution_routes.py` before the action runs.

## Audit Trail

Every governance decision is recorded by the `AuditLogger` in `backend/governance/audit.py`.

### AuditRecord Model

```python
class AuditRecord(BaseModel):
    id: str              # SHA256-derived unique ID
    timestamp: str       # ISO 8601 timestamp
    action: str          # The action that was audited
    actor: str           # Who performed the action
    resource: str        # Target resource
    outcome: str         # "permitted" or "denied"
    metadata: Dict       # Additional context (policy_id, reason, etc.)
    checksum: str        # SHA256 integrity checksum (first 32 hex chars)
```

### Integrity Checksums

Each audit record includes a SHA256 checksum computed over `id + timestamp + action + actor + resource + outcome + sequence`. This provides tamper detection: if any field is modified after creation, the checksum will not verify.

Verify a record programmatically:

```python
audit_logger.verify_record(record)  # Returns True if checksum is valid
```

### Querying the Audit Trail

**Via API:**

```http
GET /api/governance/audit
```

Returns the most recent audit records (default limit: 100):

```json
{
  "records": [
    {
      "id": "a1b2c3d4e5f6g7h8",
      "timestamp": "2025-01-18T10:00:00Z",
      "action": "runtime.register",
      "actor": "api",
      "outcome": "permitted",
      "metadata": {"policy_id": "default-allow-all"},
      "checksum": "abc123..."
    }
  ],
  "total": 1
}
```

**Via Code:**

```python
records = audit_logger.get_records(limit=50)
for record in records:
    print(f"{record.action} -> {record.outcome} at {record.timestamp}")
```

### What Gets Audited

Audit records are created in `backend/api/routes.py` when:

- A runtime registration is attempted (both permitted and denied outcomes)
- Any governance check results in a denial

The audit trail is append-only. Records cannot be modified or deleted after creation.

## Integration Flow

The full governance flow for a typical API request:

1. Request arrives at an API endpoint (e.g., `POST /api/runtime/register`)
2. The endpoint calls `governance_engine.validate_action("runtime.register")`
3. The governance engine evaluates all active policies
4. The result is logged via `audit_logger.log(action, actor, outcome)`
5. If denied: HTTP 403 is returned with the denial reason
6. If permitted: the action proceeds normally

For execution endpoints (browser, terminal, workflow, skills):

1. Request arrives at an execution endpoint (e.g., `POST /api/terminal/execute`)
2. The endpoint calls `governance_validator.validate_terminal_command(command)`
3. The validator checks safety constraints (blocklists, limits)
4. If denied: HTTP 403 with the specific reason
5. If permitted: the command executes and results are returned

## Governance Status Endpoint

Check the current governance configuration:

```http
GET /api/governance/status
```

Response:

```json
{
  "active": true,
  "policy_count": 1,
  "policies": [
    {"id": "default-allow-all", "name": "Default Allow All", "active": true}
  ]
}
```
