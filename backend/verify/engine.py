"""Verification execution engine — deterministic deployment verification."""

import hashlib
import time
from typing import Dict, List, Optional, Tuple

import httpx

from backend.governance.engine import GovernanceEngine
from backend.governance.audit import AuditLogger
from backend.runtime.context import RuntimeExecutionContext
from backend.telemetry.collector import TelemetryCollector
from backend.verify.models import (
    ApiCheckConfig,
    ApiResult,
    PageCheckConfig,
    PageResult,
    ProofManifest,
    VerifyRequest,
    VerifyRun,
    VerifyVerdict,
)
from backend.verify.persistence import VerificationPersistence
from backend.verify.browser import BrowserVerifier
from backend.verify.visual_diff import VisualDiffEngine
from backend.storage.sqlite_store import SQLiteStore
from backend.notify.webhooks import WebhookNotifier


class VerificationEngine:
    """Executes deployment verification workflows with governance and telemetry.

    Each verification run:
    1. Validates the request through governance
    2. Checks each page (HTTP GET + status + optional element presence)
    3. Checks each API endpoint (HTTP request + status + schema)
    4. Computes a score and verdict
    5. Generates a proof manifest with checksums
    6. Records telemetry
    """

    def __init__(
        self,
        context: RuntimeExecutionContext,
        governance_engine: GovernanceEngine,
        audit_logger: AuditLogger,
        telemetry_collector: TelemetryCollector,
    ):
        self._context = context
        self._governance = governance_engine
        self._audit = audit_logger
        self._telemetry = telemetry_collector
        self._runs: List[VerifyRun] = []
        self._persistence = VerificationPersistence()
        self._browser = BrowserVerifier()
        self._visual_diff = VisualDiffEngine()
        self._db = SQLiteStore()
        self._notifier = WebhookNotifier()

    async def execute(self, request: VerifyRequest) -> VerifyRun:
        """Execute a verification workflow.

        Args:
            request: Verification configuration.

        Returns:
            Complete verification run record.
        """
        start_time = self._context.now()
        timestamp = self._context.now_iso()
        execution_id = self._generate_id(request.target_url, timestamp)

        # Governance check
        decision = self._governance.validate_action(
            "verify.execute", request.target_url
        )
        self._audit.log(
            action="verify.execute",
            actor="api",
            resource=request.target_url,
            outcome="permitted" if decision.permitted else "denied",
            metadata={"policy_id": decision.policy_id or ""},
        )

        if not decision.permitted:
            run = VerifyRun(
                id=execution_id,
                timestamp=timestamp,
                target_url=request.target_url,
                verdict=VerifyVerdict.ERROR,
                score=0,
                duration_ms=0,
                error=f"Governance denied: {decision.reason}",
                governance_decisions=1,
                config=request.model_dump(),
            )
            self._runs.append(run)
            return run

        # Auto-generate page checks if none provided
        pages = request.pages
        if pages is None:
            pages = [PageCheckConfig(path="/", name="Homepage")]
        if not pages:
            pages = []

        # Auto-generate API checks if none provided
        api_checks = request.api_checks
        if api_checks is None:
            # Try common health endpoints
            api_checks = [
                ApiCheckConfig(path="/api/health", expected_status=200),
            ]
        # If explicitly empty list, skip API checks
        if not api_checks:
            api_checks = []

        # Execute page checks — use real browser if available
        page_results = await self._browser.verify_pages(
            target_url=request.target_url,
            pages=pages,
            execution_id=execution_id,
            viewport_width=request.viewport_width,
            viewport_height=request.viewport_height,
            timeout_ms=request.timeout_ms,
        )

        # If browser verification returned ERROR for all pages, fall back to HTTP
        all_browser_errors = all(
            p.status == "ERROR" and p.error == "Browser verification unavailable"
            for p in page_results
        )
        if all_browser_errors and pages:
            page_results = []
            for page_config in pages:
                result = await self._check_page(request, page_config)
                page_results.append(result)

        # Run visual diff against baselines for pages with screenshots
        visual_diffs = []
        for pr in page_results:
            if pr.screenshot_path:
                diff = self._visual_diff.compare(
                    pr.screenshot_path, request.target_url, pr.path
                )
                visual_diffs.append({"page": pr.path, **diff})
                # If regression detected, downgrade status
                if diff.get("status") == "REGRESSION" and pr.status == "PASS":
                    pr.status = "DEGRADED"

        # Execute API checks
        api_results = []
        for api_config in api_checks:
            result = await self._check_api(request, api_config)
            api_results.append(result)

        # Compute score and verdict
        score, verdict = self._compute_verdict(
            page_results, api_results, request.strict_console_errors
        )

        # Compute duration
        duration_ms = (self._context.now() - start_time) * 1000

        # Total retries
        retries_total = sum(p.retries for p in page_results) + sum(
            a.retries for a in api_results
        )

        # Total console errors
        total_console_errors = sum(p.console_errors for p in page_results)

        # Generate proof manifest
        proof = self._generate_proof(
            execution_id=execution_id,
            timestamp=timestamp,
            target_url=request.target_url,
            verdict=verdict,
            score=score,
            duration_ms=duration_ms,
            page_results=page_results,
            api_results=api_results,
        )

        # Build run record
        run = VerifyRun(
            id=execution_id,
            timestamp=timestamp,
            target_url=request.target_url,
            verdict=verdict,
            score=score,
            duration_ms=duration_ms,
            pages=page_results,
            api_results=api_results,
            total_console_errors=total_console_errors,
            proof_manifest=proof,
            config=request.model_dump(),
            governance_decisions=1,
            retries_total=retries_total,
        )

        # Persist
        self._runs.append(run)

        # Save to disk (filesystem evidence bundle)
        self._persistence.persist_run(run)

        # Save to SQLite (survives restarts)
        self._db.save_run({
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
            "pages": [p.model_dump() for p in run.pages],
            "api_results": [a.model_dump() for a in run.api_results],
            "proof_manifest": run.proof_manifest.model_dump() if run.proof_manifest else None,
            "config": run.config,
        })

        # Telemetry
        self._telemetry.increment_counter("verify.runs")
        self._telemetry.increment_counter(f"verify.verdict.{verdict.value.lower()}")
        self._telemetry.record_metric(
            "verify.duration_ms", duration_ms, {"target": request.target_url}
        )
        self._telemetry.record_metric("verify.score", float(score))

        # Notify on failure
        if self._notifier.configured:
            await self._notifier.notify({
                "id": run.id,
                "timestamp": run.timestamp,
                "target_url": run.target_url,
                "verdict": run.verdict.value,
                "score": run.score,
                "duration_ms": run.duration_ms,
            })

        return run

    async def _check_page(
        self, request: VerifyRequest, config: PageCheckConfig
    ) -> PageResult:
        """Check a single page with retry logic."""
        url = request.target_url.rstrip("/") + config.path
        name = config.name or config.path
        retries = 0

        for attempt in range(request.max_retries + 1):
            try:
                start = time.time()
                async with httpx.AsyncClient(
                    timeout=config.max_load_ms / 1000.0,
                    follow_redirects=True,
                ) as client:
                    response = await client.get(url)

                load_time_ms = (time.time() - start) * 1000

                if response.status_code >= 500:
                    if attempt < request.max_retries:
                        retries += 1
                        await self._backoff(attempt)
                        continue

                # Check title if expected
                title_match = None
                if config.expected_title:
                    title_match = config.expected_title.lower() in response.text.lower()

                # Check elements (simple text presence check for HTTP-only mode)
                elements_found = 0
                for selector in config.expected_elements:
                    if selector.lower() in response.text.lower():
                        elements_found += 1

                status = "PASS"
                if response.status_code >= 400:
                    status = "FAIL"
                elif title_match is False:
                    status = "FAIL"
                elif (
                    config.expected_elements
                    and elements_found < len(config.expected_elements)
                ):
                    status = "DEGRADED"

                return PageResult(
                    path=config.path,
                    name=name,
                    status=status,
                    load_time_ms=load_time_ms,
                    elements_found=elements_found,
                    elements_expected=len(config.expected_elements),
                    title_match=title_match,
                    retries=retries,
                )

            except httpx.TimeoutException:
                if attempt < request.max_retries:
                    retries += 1
                    await self._backoff(attempt)
                    continue
                return PageResult(
                    path=config.path,
                    name=name,
                    status="TIMEOUT",
                    error=f"Timeout after {config.max_load_ms}ms",
                    retries=retries,
                )
            except Exception as e:
                if attempt < request.max_retries:
                    retries += 1
                    await self._backoff(attempt)
                    continue
                return PageResult(
                    path=config.path,
                    name=name,
                    status="ERROR",
                    error=str(e),
                    retries=retries,
                )

        # Should not reach here, but safety fallback
        return PageResult(
            path=config.path, name=name, status="ERROR", error="Unexpected state"
        )

    async def _check_api(
        self, request: VerifyRequest, config: ApiCheckConfig
    ) -> ApiResult:
        """Check a single API endpoint with retry logic."""
        url = request.target_url.rstrip("/") + config.path
        retries = 0

        for attempt in range(request.max_retries + 1):
            try:
                start = time.time()
                async with httpx.AsyncClient(
                    timeout=config.max_response_ms / 1000.0,
                    follow_redirects=True,
                ) as client:
                    if config.method.upper() == "POST":
                        response = await client.post(url)
                    else:
                        response = await client.get(url)

                response_time_ms = (time.time() - start) * 1000

                if response.status_code >= 500 and attempt < request.max_retries:
                    retries += 1
                    await self._backoff(attempt)
                    continue

                # Check response fields
                fields_found = []
                fields_missing = []
                if config.expected_fields:
                    try:
                        body = response.json()
                        if isinstance(body, dict):
                            for field in config.expected_fields:
                                if field in body:
                                    fields_found.append(field)
                                else:
                                    fields_missing.append(field)
                    except Exception:
                        fields_missing = list(config.expected_fields)

                status = "PASS"
                if response.status_code != config.expected_status:
                    status = "FAIL"
                elif fields_missing:
                    status = "DEGRADED"

                return ApiResult(
                    path=config.path,
                    method=config.method,
                    status=status,
                    response_status=response.status_code,
                    response_time_ms=response_time_ms,
                    fields_found=fields_found,
                    fields_missing=fields_missing,
                    retries=retries,
                )

            except httpx.TimeoutException:
                if attempt < request.max_retries:
                    retries += 1
                    await self._backoff(attempt)
                    continue
                return ApiResult(
                    path=config.path,
                    method=config.method,
                    status="TIMEOUT",
                    error=f"Timeout after {config.max_response_ms}ms",
                    retries=retries,
                )
            except Exception as e:
                if attempt < request.max_retries:
                    retries += 1
                    await self._backoff(attempt)
                    continue
                return ApiResult(
                    path=config.path,
                    method=config.method,
                    status="ERROR",
                    error=str(e),
                    retries=retries,
                )

        return ApiResult(
            path=config.path,
            method=config.method,
            status="ERROR",
            error="Unexpected state",
        )

    def _compute_verdict(
        self,
        pages: List[PageResult],
        apis: List[ApiResult],
        strict_console: bool,
    ) -> Tuple[int, VerifyVerdict]:
        """Compute score (0-100) and verdict from results."""
        total_checks = len(pages) + len(apis)
        if total_checks == 0:
            return 100, VerifyVerdict.PASS

        passed = 0
        degraded = 0
        failed = 0

        for p in pages:
            if p.status == "PASS":
                passed += 1
            elif p.status == "DEGRADED":
                degraded += 1
            else:
                failed += 1

        for a in apis:
            if a.status == "PASS":
                passed += 1
            elif a.status == "DEGRADED":
                degraded += 1
            else:
                failed += 1

        # Score: PASS=100%, DEGRADED=50%, FAIL/TIMEOUT/ERROR=0%
        score = int(((passed * 100) + (degraded * 50)) / total_checks)

        # Console error penalty (if strict)
        if strict_console:
            console_errors = sum(p.console_errors for p in pages)
            if console_errors > 0:
                score = max(0, score - (console_errors * 5))

        # Verdict
        if failed > 0:
            verdict = VerifyVerdict.FAIL
        elif degraded > 0:
            verdict = VerifyVerdict.DEGRADED
        else:
            verdict = VerifyVerdict.PASS

        return score, verdict

    def _generate_proof(
        self,
        execution_id: str,
        timestamp: str,
        target_url: str,
        verdict: VerifyVerdict,
        score: int,
        duration_ms: float,
        page_results: List[PageResult],
        api_results: List[ApiResult],
    ) -> ProofManifest:
        """Generate a checksummed proof manifest."""
        # Hash each result as an artifact
        artifact_hashes: Dict[str, str] = {}
        for p in page_results:
            content = f"{p.path}:{p.status}:{p.load_time_ms}"
            h = hashlib.sha256(content.encode()).hexdigest()[:32]
            artifact_hashes[f"page:{p.path}"] = h

        for a in api_results:
            content = f"{a.path}:{a.status}:{a.response_status}"
            h = hashlib.sha256(content.encode()).hexdigest()[:32]
            artifact_hashes[f"api:{a.path}"] = h

        # Combined hash
        all_hashes = "".join(sorted(artifact_hashes.values()))
        combined = hashlib.sha256(all_hashes.encode()).hexdigest()

        manifest_id = hashlib.sha256(
            f"{execution_id}{combined}".encode()
        ).hexdigest()[:16]

        return ProofManifest(
            manifest_id=manifest_id,
            execution_id=execution_id,
            timestamp=timestamp,
            target_url=target_url,
            verdict=verdict,
            score=score,
            duration_ms=duration_ms,
            artifact_hashes=artifact_hashes,
            combined_hash=combined,
            governance_decisions=1,
            all_permitted=True,
        )

    def get_runs(self, limit: int = 50) -> List[VerifyRun]:
        """Get recent verification runs (from SQLite for persistence)."""
        db_runs = self._db.get_runs(limit)
        if db_runs:
            # Return from DB (persisted across restarts)
            results = []
            for data in db_runs:
                results.append(VerifyRun(
                    id=data["id"],
                    timestamp=data["timestamp"],
                    target_url=data["target_url"],
                    verdict=VerifyVerdict(data["verdict"]),
                    score=data["score"],
                    duration_ms=data["duration_ms"],
                    pages=[PageResult(**p) for p in data.get("pages", [])],
                    api_results=[ApiResult(**a) for a in data.get("api_results", [])],
                    proof_manifest=ProofManifest(**data["proof_manifest"]) if data.get("proof_manifest") else None,
                    config=data.get("config", {}),
                    retries_total=data.get("retries_total", 0),
                    governance_decisions=data.get("governance_decisions", 0),
                    total_console_errors=data.get("console_errors", 0),
                ))
            return results
        return self._runs[-limit:]

    def get_run(self, run_id: str) -> Optional[VerifyRun]:
        """Get a specific run by ID (checks memory first, then SQLite)."""
        # Check in-memory first (current session runs)
        for run in self._runs:
            if run.id == run_id:
                return run

        # Check SQLite (persisted from previous sessions)
        db_data = self._db.get_run(run_id)
        if db_data:
            return VerifyRun(
                id=db_data["id"],
                timestamp=db_data["timestamp"],
                target_url=db_data["target_url"],
                verdict=VerifyVerdict(db_data["verdict"]),
                score=db_data["score"],
                duration_ms=db_data["duration_ms"],
                pages=[PageResult(**p) for p in db_data.get("pages", [])],
                api_results=[ApiResult(**a) for a in db_data.get("api_results", [])],
                proof_manifest=ProofManifest(**db_data["proof_manifest"]) if db_data.get("proof_manifest") else None,
                config=db_data.get("config", {}),
                retries_total=db_data.get("retries_total", 0),
                governance_decisions=db_data.get("governance_decisions", 0),
                total_console_errors=db_data.get("console_errors", 0),
            )
        return None

    @property
    def run_count(self) -> int:
        """Total number of verification runs (from persistent storage)."""
        db_count = self._db.get_run_count()
        return db_count if db_count > 0 else len(self._runs)

    def _generate_id(self, target: str, timestamp: str) -> str:
        """Generate deterministic execution ID."""
        return hashlib.sha256(
            f"verify:{target}:{timestamp}".encode()
        ).hexdigest()[:16]

    async def _backoff(self, attempt: int) -> None:
        """Exponential backoff between retries."""
        import asyncio

        delay = min(2**attempt, 8)  # 1s, 2s, 4s, max 8s
        await asyncio.sleep(delay)
