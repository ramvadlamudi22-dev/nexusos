"""Tests for governance module - policy enforcement, permissions, audit."""

from backend.governance.audit import AuditLogger
from backend.governance.engine import GovernanceEngine
from backend.governance.models import (
    Permission,
    PermissionLevel,
    Policy,
    ValidationResult,
)
from backend.runtime.context import RuntimeExecutionContext


def make_context(fixed_time: float = 1000000.0) -> RuntimeExecutionContext:
    """Create a context with a fixed time source for deterministic testing."""
    return RuntimeExecutionContext(time_source=lambda: fixed_time)


class TestGovernanceEngine:
    """Test governance policy enforcement."""

    def test_default_deny(self):
        """Actions are denied by default when no policy allows them."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)

        result = engine.validate_action("runtime.register")

        assert result.permitted is False
        assert "default deny" in result.reason.lower() or "no policy" in result.reason.lower()

    def test_allow_policy_permits_action(self):
        """A policy with ALLOW permission permits the action."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)

        policy = Policy(
            id="policy-1",
            name="Allow Runtime Registration",
            permissions=[
                Permission(action="runtime.register", level=PermissionLevel.ALLOW)
            ],
        )
        engine.register_policy(policy)

        result = engine.validate_action("runtime.register")

        assert result.permitted is True
        assert result.policy_id == "policy-1"

    def test_deny_policy_blocks_action(self):
        """A policy with DENY permission blocks the action."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)

        policy = Policy(
            id="policy-deny",
            name="Deny All",
            permissions=[
                Permission(action="*", level=PermissionLevel.DENY)
            ],
        )
        engine.register_policy(policy)

        result = engine.validate_action("any.action")

        assert result.permitted is False
        assert result.policy_id == "policy-deny"

    def test_deny_overrides_allow(self):
        """DENY takes precedence when checked first."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)

        # Register deny policy first
        deny_policy = Policy(
            id="deny-policy",
            name="Deny Dangerous",
            permissions=[
                Permission(action="dangerous.action", level=PermissionLevel.DENY)
            ],
        )
        engine.register_policy(deny_policy)

        # Register allow policy second
        allow_policy = Policy(
            id="allow-policy",
            name="Allow All",
            permissions=[
                Permission(action="*", level=PermissionLevel.ALLOW)
            ],
        )
        engine.register_policy(allow_policy)

        result = engine.validate_action("dangerous.action")
        assert result.permitted is False

    def test_resource_specific_permission(self):
        """Permissions can target specific resources."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)

        policy = Policy(
            id="resource-policy",
            name="Resource Specific",
            permissions=[
                Permission(
                    action="read",
                    level=PermissionLevel.ALLOW,
                    resource="public-data",
                )
            ],
        )
        engine.register_policy(policy)

        # Allowed for matching resource
        result = engine.validate_action("read", resource="public-data")
        assert result.permitted is True

        # Denied for non-matching resource (no wildcard match)
        result = engine.validate_action("read", resource="private-data")
        assert result.permitted is False

    def test_inactive_policy_ignored(self):
        """Inactive policies are not evaluated."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)

        policy = Policy(
            id="inactive",
            name="Inactive Policy",
            active=False,
            permissions=[
                Permission(action="*", level=PermissionLevel.ALLOW)
            ],
        )
        engine.register_policy(policy)

        result = engine.validate_action("test.action")
        assert result.permitted is False

    def test_remove_policy(self):
        """Can remove a registered policy."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)

        policy = Policy(
            id="removable",
            name="Removable",
            permissions=[
                Permission(action="test", level=PermissionLevel.ALLOW)
            ],
        )
        engine.register_policy(policy)
        assert engine.policy_count == 1

        removed = engine.remove_policy("removable")
        assert removed is True
        assert engine.policy_count == 0

    def test_list_policies(self):
        """Can list all registered policies."""
        ctx = make_context()
        engine = GovernanceEngine(ctx)

        engine.register_policy(Policy(id="p1", name="Policy 1"))
        engine.register_policy(Policy(id="p2", name="Policy 2"))

        policies = engine.list_policies()
        assert len(policies) == 2


class TestAuditLogger:
    """Test audit logging."""

    def test_log_creates_record(self):
        """Logging creates an audit record."""
        ctx = make_context()
        logger = AuditLogger(ctx)

        record = logger.log(
            action="runtime.register",
            actor="system",
            resource="runtime-1",
            outcome="permitted",
        )

        assert record.action == "runtime.register"
        assert record.actor == "system"
        assert record.resource == "runtime-1"
        assert record.outcome == "permitted"
        assert record.checksum != ""
        assert record.id != ""

    def test_records_are_sequential(self):
        """Records have increasing IDs (different due to sequence)."""
        ctx = make_context()
        logger = AuditLogger(ctx)

        r1 = logger.log(action="action-1", actor="system")
        r2 = logger.log(action="action-2", actor="system")

        assert r1.id != r2.id
        assert logger.record_count == 2

    def test_verify_record_integrity(self):
        """Can verify audit record integrity via checksum."""
        ctx = make_context()
        logger = AuditLogger(ctx)

        record = logger.log(action="test", actor="system", resource="res")

        assert logger.verify_record(record) is True

    def test_get_records(self):
        """Can retrieve audit records."""
        ctx = make_context()
        logger = AuditLogger(ctx)

        logger.log(action="a1", actor="system")
        logger.log(action="a2", actor="system")

        records = logger.get_records()
        assert len(records) == 2
