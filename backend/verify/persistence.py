"""Verification artifact persistence — saves proof bundles to disk."""

import hashlib
import json
import os
from pathlib import Path
from typing import Optional

from backend.verify.models import VerifyRun


class VerificationPersistence:
    """Persists verification runs and proof artifacts to the filesystem.

    Each run produces a directory with:
    - manifest.json (proof manifest with checksums)
    - report.json (full structured results)
    - replay.json (replay manifest for deterministic reconstruction)
    """

    def __init__(self, base_dir: str = "artifacts/verifications"):
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def persist_run(self, run: VerifyRun) -> str:
        """Persist a verification run to disk.

        Args:
            run: The completed verification run.

        Returns:
            Path to the run directory.
        """
        run_dir = self._base_dir / run.id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Save full report
        report_path = run_dir / "report.json"
        report_data = run.model_dump()
        report_path.write_text(json.dumps(report_data, indent=2, default=str))

        # Save proof manifest
        if run.proof_manifest:
            manifest_path = run_dir / "manifest.json"
            manifest_data = run.proof_manifest.model_dump()
            manifest_path.write_text(json.dumps(manifest_data, indent=2, default=str))

        # Save replay manifest
        replay_manifest = self._build_replay_manifest(run)
        replay_path = run_dir / "replay.json"
        replay_path.write_text(json.dumps(replay_manifest, indent=2, default=str))

        # Save checksums file
        checksums = self._compute_file_checksums(run_dir)
        checksums_path = run_dir / "checksums.sha256"
        lines = [f"{h}  {name}" for name, h in sorted(checksums.items())]
        checksums_path.write_text("\n".join(lines) + "\n")

        return str(run_dir)

    def _build_replay_manifest(self, run: VerifyRun) -> dict:
        """Build a replay manifest for deterministic reconstruction."""
        return {
            "replay_version": "1.0.0",
            "execution_id": run.id,
            "timestamp": run.timestamp,
            "target_url": run.target_url,
            "config": run.config,
            "deterministic": True,
            "replay_requirements": [
                "Same target_url must be reachable",
                "Same config produces same checks",
                "Network conditions may affect timing",
            ],
            "expected_verdict": run.verdict.value,
            "expected_score": run.score,
            "page_sequence": [
                {"path": p.path, "expected_status": p.status}
                for p in run.pages
            ],
            "api_sequence": [
                {"path": a.path, "method": a.method, "expected_status": a.status}
                for a in run.api_results
            ],
        }

    def _compute_file_checksums(self, directory: Path) -> dict:
        """Compute SHA-256 checksums for all files in a directory."""
        checksums = {}
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.name != "checksums.sha256":
                content = file_path.read_bytes()
                h = hashlib.sha256(content).hexdigest()
                checksums[file_path.name] = h
        return checksums

    def get_run_path(self, run_id: str) -> Optional[Path]:
        """Get the filesystem path for a run."""
        run_dir = self._base_dir / run_id
        if run_dir.exists():
            return run_dir
        return None

    def list_persisted_runs(self) -> list:
        """List all persisted run IDs."""
        if not self._base_dir.exists():
            return []
        return [
            d.name
            for d in self._base_dir.iterdir()
            if d.is_dir() and (d / "report.json").exists()
        ]

    def verify_integrity(self, run_id: str) -> dict:
        """Verify the integrity of a persisted run's artifacts.

        Returns:
            Dictionary with verification results per file.
        """
        run_dir = self._base_dir / run_id
        checksums_path = run_dir / "checksums.sha256"

        if not checksums_path.exists():
            return {"valid": False, "error": "No checksums file found"}

        results = {}
        for line in checksums_path.read_text().strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("  ", 1)
            if len(parts) != 2:
                continue
            expected_hash, filename = parts
            file_path = run_dir / filename
            if not file_path.exists():
                results[filename] = {"valid": False, "error": "File missing"}
                continue
            actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
            results[filename] = {
                "valid": actual_hash == expected_hash,
                "expected": expected_hash[:16] + "...",
                "actual": actual_hash[:16] + "...",
            }

        all_valid = all(r["valid"] for r in results.values())
        return {"valid": all_valid, "files": results}
