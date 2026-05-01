"""
INTENTIONALLY EXPOSED DEBUG SURFACE — disable outside isolated demos.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.config import get_settings, resolve_internal_api_key

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/config")
async def debug_config() -> dict[str, Any]:
    """
    Leaks configuration material suitable for secret-scanning training labs.
    """
    s = get_settings()
    return {
        "environment": s.environment,
        "debug": s.debug,
        "database_url_host": _redact(s.database_url),
        "celery_broker_url": _redact(s.celery_broker_url),
        "admin_token_configured": bool(s.admin_token),
        "resolved_internal_key_tail": resolve_internal_api_key()[-6:],
        "HARDCODED_FALLBACK_API_KEY": s.HARDCODED_FALLBACK_API_KEY,
    }


def _redact(url: str) -> str:
    if "@" in url:
        return url.split("@", 1)[-1]
    return url
