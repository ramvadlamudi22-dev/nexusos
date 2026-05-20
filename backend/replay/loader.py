"""Replay loader - interface for loading and replaying recorded operations."""

from typing import List, Optional, Protocol

from backend.replay.models import ReplayRecord


class ReplayLoader:
    """Loads and provides access to replay recordings.

    This is the interface for replaying recorded operations.
    Records are loaded in sequence order for deterministic replay.
    """

    def __init__(self) -> None:
        """Initialize the replay loader."""
        self._records: List[ReplayRecord] = []
        self._position: int = 0

    def load(self, records: List[ReplayRecord]) -> None:
        """Load replay records for replay.

        Records are sorted by sequence number to ensure deterministic ordering.

        Args:
            records: List of replay records to load.
        """
        self._records = sorted(records, key=lambda r: r.sequence)
        self._position = 0

    def next(self) -> Optional[ReplayRecord]:
        """Get the next record in the replay sequence.

        Returns:
            The next ReplayRecord, or None if no more records.
        """
        if self._position >= len(self._records):
            return None
        record = self._records[self._position]
        self._position += 1
        return record

    def peek(self) -> Optional[ReplayRecord]:
        """Peek at the next record without advancing the position.

        Returns:
            The next ReplayRecord, or None if no more records.
        """
        if self._position >= len(self._records):
            return None
        return self._records[self._position]

    def reset(self) -> None:
        """Reset the replay position to the beginning."""
        self._position = 0

    @property
    def remaining(self) -> int:
        """Number of remaining records to replay."""
        return len(self._records) - self._position

    @property
    def total(self) -> int:
        """Total number of loaded records."""
        return len(self._records)

    @property
    def is_complete(self) -> bool:
        """Whether all records have been replayed."""
        return self._position >= len(self._records)
