"""Real Playwright browser verification — renders pages, captures screenshots, detects errors."""

import asyncio
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.verify.models import PageCheckConfig, PageResult


class BrowserVerifier:
    """Executes real browser verification using Playwright via Node.js subprocess.

    Renders pages in Chromium, captures screenshots, detects console errors,
    and validates page content with real JavaScript execution.
    """

    def __init__(self, artifacts_dir: str = "artifacts/evidence"):
        self._artifacts_dir = Path(artifacts_dir)
        self._artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._node_script = Path(__file__).parent / "browser_worker.js"

    async def verify_pages(
        self,
        target_url: str,
        pages: List[PageCheckConfig],
        execution_id: str,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        timeout_ms: int = 30000,
    ) -> List[PageResult]:
        """Verify pages using real Playwright browser rendering.

        Args:
            target_url: Base URL to verify.
            pages: Page configurations to check.
            execution_id: Unique execution ID for artifact naming.
            viewport_width: Browser viewport width.
            viewport_height: Browser viewport height.
            timeout_ms: Per-page timeout.

        Returns:
            List of PageResult with screenshots and console error data.
        """
        # Build the verification task
        task = {
            "target_url": target_url,
            "execution_id": execution_id,
            "artifacts_dir": str(self._artifacts_dir / execution_id),
            "viewport": {"width": viewport_width, "height": viewport_height},
            "timeout_ms": timeout_ms,
            "pages": [
                {
                    "path": p.path,
                    "name": p.name or p.path,
                    "expected_title": p.expected_title,
                    "expected_elements": p.expected_elements,
                }
                for p in pages
            ],
        }

        # Execute via Node.js subprocess
        result = await self._run_browser_worker(task)

        if result is None:
            # Browser worker failed entirely — fall back to HTTP results
            return [
                PageResult(
                    path=p.path,
                    name=p.name or p.path,
                    status="ERROR",
                    error="Browser verification unavailable",
                )
                for p in pages
            ]

        # Parse results
        page_results = []
        for page_data in result.get("pages", []):
            page_results.append(
                PageResult(
                    path=page_data["path"],
                    name=page_data["name"],
                    status=page_data["status"],
                    load_time_ms=page_data.get("load_time_ms", 0),
                    console_errors=page_data.get("console_errors", 0),
                    console_error_messages=page_data.get("console_error_messages", []),
                    elements_found=page_data.get("elements_found", 0),
                    elements_expected=page_data.get("elements_expected", 0),
                    title_match=page_data.get("title_match"),
                    screenshot_path=page_data.get("screenshot_path"),
                    error=page_data.get("error"),
                )
            )

        return page_results

    async def _run_browser_worker(self, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run the Node.js browser worker subprocess."""
        # Ensure the worker script exists
        if not self._node_script.exists():
            return None

        # Write task to temp file
        task_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, dir=tempfile.gettempdir()
        )
        json.dump(task, task_file)
        task_file.close()

        try:
            proc = await asyncio.create_subprocess_exec(
                "node",
                str(self._node_script),
                task_file.name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(Path(__file__).parent.parent.parent),
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=120
            )

            if proc.returncode != 0:
                return None

            # Parse JSON output from stdout
            output = stdout.decode().strip()
            if output:
                return json.loads(output)
            return None

        except (asyncio.TimeoutError, json.JSONDecodeError, FileNotFoundError):
            return None
        finally:
            try:
                os.unlink(task_file.name)
            except OSError:
                pass
