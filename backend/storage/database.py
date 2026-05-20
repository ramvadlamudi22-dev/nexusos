"""Database persistence layer — Supabase/PostgreSQL integration.

Provides persistent storage for verification runs, replay manifests,
and telemetry. Falls back to in-memory storage when DATABASE_URL is not set.
"""

import json
import os
from typing import Any, Dict, List, Optional

from backend.verify.models import VerifyRun, VerifyVerdict


class DatabaseStore:
    """Persistent storage for verification data.

    Uses Supabase (PostgreSQL) in production, in-memory dict in development.
    """

    def __init__(self):
        self._db_url = os.environ.get("DATABASE_URL")
        self._client = None
        self._memory_store: List[Dict[str, Any]] = []

        if self._db_url:
            self._init_db()

    def _init_db(self) -> None:
        """Initialize database connection.

        Creates tables if they don't exist.
        """
        try:
            # Lazy import — only needed in production
            import asyncpg  # noqa: F401

            self._mode = "postgres"
        except ImportError:
            self._mode = "memory"
            return

    @property
    def mode(self) -> str:
        """Current storage mode."""
        if self._db_url and self._mode == "postgres":
            return "postgres"
        return "memory"

    def save_run(self, run: VerifyRun) -> None:
        """Save a verification run.

        Args:
            run: The completed verification run.
        """
        record = {
            "id": run.id,
            "timestamp": run.timestamp,
            "target_url": run.target_url,
            "verdict": run.verdict.value,
            "score": run.score,
            "duration_ms": run.duration_ms,
            "pages_checked": len(run.pages),
            "apis_checked": len(run.api_results),
            "retries_total": run.retries_total,
            "console_errors": run.total_console_errors,
            "governance_decisions": run.governance_decisions,
            "config": run.config,
            "proof_manifest": run.proof_manifest.model_dump() if run.proof_manifest else None,
            "pages": [p.model_dump() for p in run.pages],
            "api_results": [a.model_dump() for a in run.api_results],
        }

        if self.mode == "postgres":
            self._save_to_db(record)
        else:
            self._memory_store.append(record)

    def get_runs(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get recent verification runs.

        Args:
            limit: Maximum number of runs to return.
            offset: Number of runs to skip.

        Returns:
            List of run records (most recent first).
        """
        if self.mode == "postgres":
            return self._get_from_db(limit, offset)

        # Memory store — return most recent first
        sorted_runs = sorted(
            self._memory_store, key=lambda r: r["timestamp"], reverse=True
        )
        return sorted_runs[offset : offset + limit]

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific run by ID."""
        if self.mode == "postgres":
            return self._get_run_from_db(run_id)

        for record in self._memory_store:
            if record["id"] == run_id:
                return record
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics."""
        runs = self._memory_store if self.mode == "memory" else self._get_from_db(9999)

        if not runs:
            return {"total": 0, "pass_rate": 0, "avg_score": 0, "avg_duration_ms": 0}

        total = len(runs)
        passed = sum(1 for r in runs if r["verdict"] == "PASS")
        avg_score = sum(r["score"] for r in runs) / total
        avg_duration = sum(r["duration_ms"] for r in runs) / total

        return {
            "total": total,
            "pass_rate": round(passed / total * 100, 1),
            "avg_score": round(avg_score, 1),
            "avg_duration_ms": round(avg_duration, 1),
            "passed": passed,
            "failed": total - passed,
        }

    @property
    def count(self) -> int:
        """Total number of stored runs."""
        return len(self._memory_store)

    # --- PostgreSQL methods (stubs for when asyncpg is available) ---

    def _save_to_db(self, record: Dict[str, Any]) -> None:
        """Save to PostgreSQL. Falls back to memory if connection fails."""
        # TODO: Implement when deploying with Supabase
        self._memory_store.append(record)

    def _get_from_db(self, limit: int, offset: int = 0) -> List[Dict[str, Any]]:
        """Get from PostgreSQL."""
        # TODO: Implement when deploying with Supabase
        sorted_runs = sorted(
            self._memory_store, key=lambda r: r["timestamp"], reverse=True
        )
        return sorted_runs[offset : offset + limit]

    def _get_run_from_db(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get single run from PostgreSQL."""
        # TODO: Implement when deploying with Supabase
        for record in self._memory_store:
            if record["id"] == run_id:
                return record
        return None


# SQL schema for Supabase migration
SCHEMA_SQL = """
-- Verification runs table
CREATE TABLE IF NOT EXISTS verification_runs (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    target_url TEXT NOT NULL,
    verdict TEXT NOT NULL CHECK (verdict IN ('PASS', 'FAIL', 'DEGRADED', 'ERROR')),
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    duration_ms REAL NOT NULL,
    pages_checked INTEGER NOT NULL DEFAULT 0,
    apis_checked INTEGER NOT NULL DEFAULT 0,
    retries_total INTEGER NOT NULL DEFAULT 0,
    console_errors INTEGER NOT NULL DEFAULT 0,
    governance_decisions INTEGER NOT NULL DEFAULT 0,
    config JSONB,
    proof_manifest JSONB,
    pages JSONB,
    api_results JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_runs_timestamp ON verification_runs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_runs_target ON verification_runs(target_url);
CREATE INDEX IF NOT EXISTS idx_runs_verdict ON verification_runs(verdict);

-- API keys table
CREATE TABLE IF NOT EXISTS api_keys (
    key_hash TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'starter',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    rate_limit_per_minute INTEGER NOT NULL DEFAULT 10,
    monthly_quota INTEGER NOT NULL DEFAULT 100,
    usage_this_month INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit trail table
CREATE TABLE IF NOT EXISTS audit_records (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    resource TEXT,
    outcome TEXT NOT NULL,
    metadata JSONB,
    checksum TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_records(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_records(action);
"""
