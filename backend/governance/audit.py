"""Audit logger - immutable audit records with checksums."""

import hashlib
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.runtime.context import RuntimeExecutionContext


class AuditRecord(BaseModel):
    """An immutable audit record with integrity checksum."""

    id: str
    timestamp: str
    action: str
    actor: str
    resource: str = ""
    outcome: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    checksum: str = ""


class AuditLogger:
    """Produces immutable audit records for all governance decisions.

    Each record includes a checksum for integrity verification.
    Records are append-only and cannot be modified after creation.
    """

    def __init__(self, context: RuntimeExecutionContext):
        """Initialize the audit logger.

        Args:
            context: Execution context providing time source.
        """
        self._context = context
        self._records: List[AuditRecord] = []
        self._sequence: int = 0

    def log(
        self,
        action: str,
        actor: str,
        resource: str = "",
        outcome: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditRecord:
        """Create an immutable audit record.

        Args:
            action: The action being audited.
            actor: Who performed the action.
            resource: The target resource.
            outcome: The result (e.g., "permitted", "denied").
            metadata: Additional context.

        Returns:
            The created AuditRecord.
        """
        self._sequence += 1
        timestamp = self._context.now_iso()

        record_id = hashlib.sha256(
            f"{action}{actor}{self._sequence}{timestamp}".encode("utf-8")
        ).hexdigest()[:16]

        # Compute checksum over record content for integrity
        checksum_content = f"{record_id}{timestamp}{action}{actor}{resource}{outcome}{self._sequence}"
        checksum = hashlib.sha256(checksum_content.encode("utf-8")).hexdigest()[:32]

        record = AuditRecord(
            id=record_id,
            timestamp=timestamp,
            action=action,
            actor=actor,
            resource=resource,
            outcome=outcome,
            metadata=metadata or {},
            checksum=checksum,
        )

        self._records.append(record)
        return record

    def get_records(self, limit: int = 100) -> List[AuditRecord]:
        """Get recent audit records.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of recent audit records.
        """
        return self._records[-limit:]

    def verify_record(self, record: AuditRecord) -> bool:
        """Verify the integrity of an audit record.

        Args:
            record: The record to verify.

        Returns:
            True if the checksum is valid, False otherwise.
        """
        checksum_content = (
            f"{record.id}{record.timestamp}{record.action}"
            f"{record.actor}{record.resource}{record.outcome}"
            f"{self._get_sequence_for_record(record)}"
        )
        expected = hashlib.sha256(checksum_content.encode("utf-8")).hexdigest()[:32]
        return record.checksum == expected

    def _get_sequence_for_record(self, record: AuditRecord) -> int:
        """Get the sequence number for a record based on its position."""
        for i, r in enumerate(self._records):
            if r.id == record.id:
                return i + 1
        return 0

    @property
    def record_count(self) -> int:
        """Get the total number of audit records."""
        return len(self._records)
