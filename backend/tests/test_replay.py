"""Tests for replay module - recording, deterministic replay."""

from backend.replay.loader import ReplayLoader
from backend.replay.models import ReplayRecord
from backend.replay.recorder import ReplayRecorder
from backend.runtime.context import RuntimeExecutionContext


def make_context(fixed_time: float = 1000000.0) -> RuntimeExecutionContext:
    """Create a context with a fixed time source for deterministic testing."""
    return RuntimeExecutionContext(time_source=lambda: fixed_time)


class TestReplayRecorder:
    """Test deterministic operation recording."""

    def test_record_operation(self):
        """Can record an operation with inputs and outputs."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)

        record = recorder.record(
            operation="runtime.register",
            inputs={"name": "test-rt"},
            outputs={"id": "abc123"},
        )

        assert record.operation == "runtime.register"
        assert record.inputs == {"name": "test-rt"}
        assert record.outputs == {"id": "abc123"}
        assert record.sequence == 1
        assert record.checksum != ""
        assert record.id != ""

    def test_sequence_increments(self):
        """Each recording increments the sequence number."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)

        r1 = recorder.record(operation="op1")
        r2 = recorder.record(operation="op2")
        r3 = recorder.record(operation="op3")

        assert r1.sequence == 1
        assert r2.sequence == 2
        assert r3.sequence == 3

    def test_deterministic_records(self):
        """Same inputs produce same records with same time source."""
        ctx = make_context(fixed_time=1000000.0)
        recorder1 = ReplayRecorder(ctx)
        recorder2 = ReplayRecorder(ctx)

        r1 = recorder1.record(operation="test", inputs={"a": 1})
        r2 = recorder2.record(operation="test", inputs={"a": 1})

        # Same time, same sequence, same operation -> same ID and checksum
        assert r1.id == r2.id
        assert r1.checksum == r2.checksum

    def test_get_records(self):
        """Can retrieve recorded operations."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)

        recorder.record(operation="op1")
        recorder.record(operation="op2")

        records = recorder.get_records()
        assert len(records) == 2
        assert records[0].operation == "op1"
        assert records[1].operation == "op2"

    def test_get_record_by_sequence(self):
        """Can retrieve a record by sequence number."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)

        recorder.record(operation="op1")
        recorder.record(operation="op2")

        found = recorder.get_record_by_sequence(2)
        assert found is not None
        assert found.operation == "op2"

    def test_record_count(self):
        """record_count tracks total recordings."""
        ctx = make_context()
        recorder = ReplayRecorder(ctx)

        assert recorder.record_count == 0
        recorder.record(operation="test")
        assert recorder.record_count == 1


class TestReplayLoader:
    """Test replay loading and sequential access."""

    def test_load_and_iterate(self):
        """Can load records and iterate through them."""
        loader = ReplayLoader()
        records = [
            ReplayRecord(
                id="r1", operation="op1", timestamp="t1", sequence=1, checksum="c1"
            ),
            ReplayRecord(
                id="r2", operation="op2", timestamp="t2", sequence=2, checksum="c2"
            ),
        ]

        loader.load(records)

        r1 = loader.next()
        assert r1 is not None
        assert r1.operation == "op1"

        r2 = loader.next()
        assert r2 is not None
        assert r2.operation == "op2"

        r3 = loader.next()
        assert r3 is None

    def test_sorts_by_sequence(self):
        """Loaded records are sorted by sequence for deterministic replay."""
        loader = ReplayLoader()
        records = [
            ReplayRecord(
                id="r3", operation="op3", timestamp="t3", sequence=3, checksum="c3"
            ),
            ReplayRecord(
                id="r1", operation="op1", timestamp="t1", sequence=1, checksum="c1"
            ),
            ReplayRecord(
                id="r2", operation="op2", timestamp="t2", sequence=2, checksum="c2"
            ),
        ]

        loader.load(records)

        assert loader.next().operation == "op1"
        assert loader.next().operation == "op2"
        assert loader.next().operation == "op3"

    def test_peek_does_not_advance(self):
        """Peek returns next record without advancing position."""
        loader = ReplayLoader()
        records = [
            ReplayRecord(
                id="r1", operation="op1", timestamp="t1", sequence=1, checksum="c1"
            ),
        ]
        loader.load(records)

        peeked = loader.peek()
        assert peeked is not None
        assert peeked.operation == "op1"

        # Position not advanced
        next_record = loader.next()
        assert next_record.operation == "op1"

    def test_reset(self):
        """Can reset to replay from the beginning."""
        loader = ReplayLoader()
        records = [
            ReplayRecord(
                id="r1", operation="op1", timestamp="t1", sequence=1, checksum="c1"
            ),
            ReplayRecord(
                id="r2", operation="op2", timestamp="t2", sequence=2, checksum="c2"
            ),
        ]
        loader.load(records)

        loader.next()
        loader.next()
        assert loader.is_complete is True

        loader.reset()
        assert loader.is_complete is False
        assert loader.next().operation == "op1"

    def test_remaining_count(self):
        """remaining tracks how many records are left."""
        loader = ReplayLoader()
        records = [
            ReplayRecord(
                id="r1", operation="op1", timestamp="t1", sequence=1, checksum="c1"
            ),
            ReplayRecord(
                id="r2", operation="op2", timestamp="t2", sequence=2, checksum="c2"
            ),
        ]
        loader.load(records)

        assert loader.remaining == 2
        assert loader.total == 2

        loader.next()
        assert loader.remaining == 1
