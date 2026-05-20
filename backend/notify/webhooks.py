"""Webhook notification system — alerts on verification failures."""

import os
from typing import Any, Dict, Optional

import httpx


class WebhookNotifier:
    """Sends notifications via webhooks on verification events.

    Supports: generic webhooks, Slack, Discord.
    Configured via environment variables.
    """

    def __init__(self):
        self._webhook_url = os.environ.get("NEXUSOS_WEBHOOK_URL")
        self._slack_url = os.environ.get("NEXUSOS_SLACK_WEBHOOK")
        self._discord_url = os.environ.get("NEXUSOS_DISCORD_WEBHOOK")
        self._notify_on = os.environ.get("NEXUSOS_NOTIFY_ON", "FAIL,ERROR")

    @property
    def configured(self) -> bool:
        return bool(self._webhook_url or self._slack_url or self._discord_url)

    def should_notify(self, verdict: str) -> bool:
        triggers = [t.strip().upper() for t in self._notify_on.split(",")]
        return verdict.upper() in triggers

    async def notify(self, run_data: Dict[str, Any]) -> None:
        """Send notification for a verification run.

        Args:
            run_data: Verification run result data.
        """
        verdict = run_data.get("verdict", "UNKNOWN")
        if not self.should_notify(verdict):
            return

        target = run_data.get("target_url", "unknown")
        score = run_data.get("score", 0)
        duration = run_data.get("duration_ms", 0)

        message = (
            f"{'🚨' if verdict == 'FAIL' else '⚠️'} NexusOS Verification {verdict}\n"
            f"Target: {target}\n"
            f"Score: {score}/100 | Duration: {duration/1000:.1f}s"
        )

        # Generic webhook
        if self._webhook_url:
            await self._send_webhook(self._webhook_url, {
                "event": "verification.completed",
                "verdict": verdict,
                "target_url": target,
                "score": score,
                "duration_ms": duration,
                "run_id": run_data.get("id"),
                "timestamp": run_data.get("timestamp"),
            })

        # Slack
        if self._slack_url:
            await self._send_slack(message, run_data)

        # Discord
        if self._discord_url:
            await self._send_discord(message)

    async def _send_webhook(self, url: str, payload: Dict[str, Any]) -> None:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(url, json=payload)
        except Exception:
            pass  # Don't let notification failures break verification

    async def _send_slack(self, message: str, run_data: Dict[str, Any]) -> None:
        verdict = run_data.get("verdict", "")
        color = "#36a64f" if verdict == "PASS" else "#ff0000"

        payload = {
            "attachments": [{
                "color": color,
                "title": f"NexusOS Verification: {verdict}",
                "text": message,
                "fields": [
                    {"title": "Target", "value": run_data.get("target_url", ""), "short": True},
                    {"title": "Score", "value": f"{run_data.get('score', 0)}/100", "short": True},
                ],
                "footer": "NexusOS Operational Trust Platform",
            }]
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(self._slack_url, json=payload)
        except Exception:
            pass

    async def _send_discord(self, message: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(self._discord_url, json={"content": message})
        except Exception:
            pass
