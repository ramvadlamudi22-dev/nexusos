"""Replay recorder - records all runtime operations deterministically."""

import hashlib
from typing import Any, Dict, List, Optional

from backend.replay.models import ReplayRecord
from backend.runtime.context import RuntimeExecutionContext


class ReplayRecorder:
    """Records all runtime operations for deterministic replay.

    Each record includes a sequence number and checksum for verification.
    Operations are recorded in order and can be replayed deterministically.
    """

    def __init__(self, context: RuntimeExecutionContext):
        """Initialize the replay recorder.

        Args:
            context: Execution context providing time source.
        """
        self._context = context
        self._records: List[ReplayRecord] = []
        self._sequence: int = 0

    def record(
        self,
        operation: str,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
    ) -> ReplayRecord:
        """Record an operation.

        Args:
            operation: Name of the operation.
            inputs: Input parameters.
            outputs: Output results.

        Returns:
            The created ReplayRecord.
        """
        self._sequence += 1
        timestamp = self._context.now_iso()

        record_id = hashlib.sha256(
            f"{operation}{self._sequence}{inputs}".encode("utf-8")
        ).hexdigest()[:16]

        # Compute checksum over record content
        checksum_content = f"{record_id}{operation}{self._sequence}{inputs}"
        checksum = hashlib.sha256(checksum_content.encode("utf-8")).hexdigest()[:32]

        record = ReplayRecord(
            id=record_id,
            operation=operation,
            inputs=inputs or {},
            outputs=outputs or {},
            timestamp=timestamp,
            sequence=self._sequence,
            checksum=checksum,
        )

        self._records.append(record)
        return record

    def get_records(self, limit: int = 100) -> List[ReplayRecord]:
        """Get recorded operations.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of replay records in order.
        """
        return self._records[-limit:]

    def get_record_by_sequence(self, sequence: int) -> Optional[ReplayRecord]:
        """Get a record by its sequence number.

        Args:
            sequence: The sequence number to look up.

        Returns:
            The record if found, None otherwise.
        """
        for record in self._records:
            if record.sequence == sequence:
                return record
        return None

    @property
    def record_count(self) -> int:
        """Total number of recorded operations."""
        return len(self._records)

    @property
    def current_sequence(self) -> int:
        """Current sequence number."""
        return self._sequence
