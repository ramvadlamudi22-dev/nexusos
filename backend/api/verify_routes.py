"""FastAPI router for the verification endpoint."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Header

from backend.auth.api_keys import AuthManager
from backend.verify.engine import VerificationEngine
from backend.verify.models import VerifyRequest
from backend.verify.templates import list_templates, build_request_from_template


def create_verify_router(engine: VerificationEngine, auth: AuthManager) -> APIRouter:
    """Create the verification API router.

    Args:
        engine: The verification execution engine.
        auth: Authentication manager.

    Returns:
        Configured APIRouter with verify endpoints.
    """
    router = APIRouter(prefix="/api")

    def _authenticate(authorization: str = Header(default=None)):
        """Validate API key and rate limit."""
        authenticated, api_key, error = auth.authenticate(authorization)
        if not authenticated:
            raise HTTPException(status_code=401, detail=error)
        allowed, rate_error = auth.check_rate_limit(api_key)
        if not allowed:
            raise HTTPException(status_code=429, detail=rate_error)
        return api_key

    @router.post("/verify")
    async def run_verification(
        request: VerifyRequest,
        authorization: str = Header(default=None),
    ) -> Dict[str, Any]:
        """Execute a deployment verification workflow.

        Verifies pages load correctly, APIs respond as expected,
        and produces a checksummed proof manifest.
        """
        _authenticate(authorization)
        run = await engine.execute(request)
        return run.model_dump()

    @router.post("/verify/template/{template_id}")
    async def run_template_verification(
        template_id: str,
        target_url: str,
        authorization: str = Header(default=None),
    ) -> Dict[str, Any]:
        """Execute a verification using a predefined template.

        Args:
            template_id: Template to use (smoke-test, full-site, api-only, etc.)
            target_url: Target URL to verify.
        """
        _authenticate(authorization)
        try:
            request = build_request_from_template(template_id, target_url)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        run = await engine.execute(request)
        return run.model_dump()

    @router.get("/verify/templates")
    def get_templates() -> Dict[str, Any]:
        """List available verification templates."""
        return {"templates": list_templates()}

    @router.get("/verify/runs")
    def list_verification_runs() -> Dict[str, Any]:
        """List recent verification runs."""
        runs = engine.get_runs()
        return {
            "runs": [
                {
                    "id": r.id,
                    "timestamp": r.timestamp,
                    "target_url": r.target_url,
                    "verdict": r.verdict.value,
                    "score": r.score,
                    "duration_ms": r.duration_ms,
                    "pages_checked": len(r.pages),
                    "apis_checked": len(r.api_results),
                    "retries": r.retries_total,
                }
                for r in reversed(runs)
            ],
            "total": engine.run_count,
        }

    @router.get("/verify/runs/{run_id}")
    def get_verification_run(run_id: str) -> Dict[str, Any]:
        """Get a specific verification run with full details."""
        run = engine.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Verification run not found")
        return run.model_dump()

    @router.get("/verify/runs/{run_id}/proof")
    def get_proof_manifest(run_id: str) -> Dict[str, Any]:
        """Get the proof manifest for a verification run."""
        run = engine.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Verification run not found")
        if run.proof_manifest is None:
            raise HTTPException(status_code=404, detail="No proof manifest available")
        return run.proof_manifest.model_dump()

    @router.get("/verify/runs/{run_id}/verify-integrity")
    def verify_run_integrity(run_id: str) -> Dict[str, Any]:
        """Verify the integrity of a persisted verification run's artifacts."""
        from backend.verify.persistence import VerificationPersistence

        persistence = VerificationPersistence()
        result = persistence.verify_integrity(run_id)
        return {"run_id": run_id, **result}

    @router.get("/verify/baselines")
    def list_baselines() -> Dict[str, Any]:
        """List all stored visual baselines."""
        from backend.verify.visual_diff import VisualDiffEngine
        diff_engine = VisualDiffEngine()
        return {"baselines": diff_engine.list_baselines()}

    @router.post("/verify/baselines/update")
    def update_baseline(target_url: str, page_path: str, run_id: str) -> Dict[str, Any]:
        """Update a baseline from a verification run's screenshot."""
        run = engine.get_run(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Run not found")

        from backend.verify.visual_diff import VisualDiffEngine
        diff_engine = VisualDiffEngine()

        for page in run.pages:
            if page.path == page_path and page.screenshot_path:
                updated = diff_engine.update_baseline(page.screenshot_path, target_url, page_path)
                if updated:
                    return {"status": "updated", "target_url": target_url, "page_path": page_path}

        raise HTTPException(status_code=404, detail="Screenshot not found for page")

    @router.get("/verify/runs/{run_id}/evidence")
    def get_evidence_bundle(run_id: str) -> Dict[str, Any]:
        """Get the evidence bundle file listing for a verification run."""
        from pathlib import Path
        from backend.verify.persistence import VerificationPersistence
        persistence = VerificationPersistence()
        run_path = persistence.get_run_path(run_id)

        files = []
        if run_path is not None:
            for f in run_path.iterdir():
                if f.is_file():
                    files.append({
                        "name": f.name,
                        "size_bytes": f.stat().st_size,
                    })

        # Check for screenshots in evidence dir
        evidence_dir = Path("artifacts/evidence") / run_id
        screenshots = []
        if evidence_dir.exists():
            for f in evidence_dir.iterdir():
                if f.suffix == ".png":
                    screenshots.append({
                        "name": f.name,
                        "size_bytes": f.stat().st_size,
                    })

        if not files and not screenshots:
            raise HTTPException(status_code=404, detail="No evidence found for this run")

        return {
            "run_id": run_id,
            "files": files,
            "screenshots": screenshots,
            "total_artifacts": len(files) + len(screenshots),
        }

    @router.get("/verify/stats")
    def get_verification_stats() -> Dict[str, Any]:
        """Get verification execution statistics."""
        runs = engine.get_runs()
        if not runs:
            return {
                "total_runs": 0,
                "pass_rate": 0,
                "avg_duration_ms": 0,
                "avg_score": 0,
                "total_retries": 0,
                "verdicts": {},
            }

        verdicts: Dict[str, int] = {}
        total_duration = 0.0
        total_score = 0
        total_retries = 0

        for run in runs:
            v = run.verdict.value
            verdicts[v] = verdicts.get(v, 0) + 1
            total_duration += run.duration_ms
            total_score += run.score
            total_retries += run.retries_total

        total = len(runs)
        pass_count = verdicts.get("PASS", 0)

        return {
            "total_runs": total,
            "pass_rate": round(pass_count / total * 100, 1) if total > 0 else 0,
            "avg_duration_ms": round(total_duration / total, 1),
            "avg_score": round(total_score / total, 1),
            "total_retries": total_retries,
            "verdicts": verdicts,
        }

    return router
