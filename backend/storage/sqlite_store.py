"""SQLite persistent storage — survives restarts, zero external dependencies."""

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional


class SQLiteStore:
    """Persistent storage using SQLite. Zero configuration, survives restarts.

    Thread-safe via connection-per-thread pattern.
    """

    def __init__(self, db_path: str = "data/nexusos.db"):
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(str(self._db_path))
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA busy_timeout=5000")
        return self._local.conn

    def _init_schema(self) -> None:
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS verification_runs (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                target_url TEXT NOT NULL,
                verdict TEXT NOT NULL,
                score INTEGER NOT NULL,
                duration_ms REAL NOT NULL,
                pages_checked INTEGER DEFAULT 0,
                apis_checked INTEGER DEFAULT 0,
                retries_total INTEGER DEFAULT 0,
                console_errors INTEGER DEFAULT 0,
                governance_decisions INTEGER DEFAULT 0,
                data JSON NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_runs_ts ON verification_runs(timestamp DESC);
            CREATE INDEX IF NOT EXISTS idx_runs_target ON verification_runs(target_url);

            CREATE TABLE IF NOT EXISTS audit_records (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                action TEXT NOT NULL,
                actor TEXT NOT NULL,
                resource TEXT DEFAULT '',
                outcome TEXT NOT NULL,
                metadata JSON,
                checksum TEXT NOT NULL,
                sequence INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_records(timestamp DESC);

            CREATE TABLE IF NOT EXISTS baselines (
                key TEXT PRIMARY KEY,
                target_url TEXT NOT NULL,
                page_path TEXT NOT NULL,
                screenshot_hash TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            );
        """)
        conn.commit()

    # --- Verification Runs ---

    def save_run(self, run_data: Dict[str, Any]) -> None:
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO verification_runs
               (id, timestamp, target_url, verdict, score, duration_ms,
                pages_checked, apis_checked, retries_total, console_errors,
                governance_decisions, data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_data["id"],
                run_data["timestamp"],
                run_data["target_url"],
                run_data["verdict"],
                run_data["score"],
                run_data["duration_ms"],
                run_data.get("pages_checked", 0),
                run_data.get("apis_checked", 0),
                run_data.get("retries_total", 0),
                run_data.get("console_errors", 0),
                run_data.get("governance_decisions", 0),
                json.dumps(run_data),
            ),
        )
        conn.commit()

    def get_runs(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT data FROM verification_runs ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [json.loads(row["data"]) for row in rows]

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT data FROM verification_runs WHERE id = ?", (run_id,)
        ).fetchone()
        if row:
            return json.loads(row["data"])
        return None

    def get_run_count(self) -> int:
        conn = self._get_conn()
        row = conn.execute("SELECT COUNT(*) as cnt FROM verification_runs").fetchone()
        return row["cnt"]

    def get_stats(self) -> Dict[str, Any]:
        conn = self._get_conn()
        total = self.get_run_count()
        if total == 0:
            return {"total": 0, "pass_rate": 0, "avg_score": 0, "avg_duration_ms": 0}

        row = conn.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN verdict = 'PASS' THEN 1 ELSE 0 END) as passed,
                AVG(score) as avg_score,
                AVG(duration_ms) as avg_duration
            FROM verification_runs
        """).fetchone()

        return {
            "total": row["total"],
            "pass_rate": round((row["passed"] / row["total"]) * 100, 1) if row["total"] > 0 else 0,
            "avg_score": round(row["avg_score"], 1),
            "avg_duration_ms": round(row["avg_duration"], 1),
        }

    # --- Audit Records ---

    def save_audit_record(self, record: Dict[str, Any]) -> None:
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO audit_records
               (id, timestamp, action, actor, resource, outcome, metadata, checksum, sequence)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record["id"],
                record["timestamp"],
                record["action"],
                record["actor"],
                record.get("resource", ""),
                record["outcome"],
                json.dumps(record.get("metadata", {})),
                record["checksum"],
                record.get("sequence", 0),
            ),
        )
        conn.commit()

    def get_audit_records(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM audit_records ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]
