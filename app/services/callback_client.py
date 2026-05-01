"""
LOS / CRM callback integration.

INTENTIONAL SSRF DEMO: user-supplied `los_callback_url` is requested from the
worker network without scheme/host validation or egress controls.
"""

from __future__ import annotations

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def fetch_callback_preview(url: str) -> dict:
    """
    Perform an HTTP GET and return metadata + truncated body.

    This is unsafe by design for security training exercises.
    """
    settings = get_settings()
    timeout = float(settings.default_callback_timeout_seconds)
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url)
            text = resp.text
            snippet = text[:2000]
            return {
                "ok": True,
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "body_snippet": snippet,
                "url_requested": str(resp.url),
            }
    except Exception as exc:  # noqa: BLE001 — broad catch mirrors naive prod code
        logger.exception("callback fetch failed")
        return {"ok": False, "error": str(exc), "url_requested": url}
