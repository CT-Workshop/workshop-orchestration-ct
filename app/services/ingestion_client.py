"""Client for the doc-ingestion service (workshop cross-service contract)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def search_closing_documents(
    *,
    tenant_id: str,
    q: str | None = None,
) -> list[dict[str, Any]]:
    """Return metadata rows uploaded by closing-orchestration."""
    settings = get_settings()
    base = settings.ingestion_service_url.rstrip("/")
    params: dict[str, str | int] = {
        "source_system": "closing-orchestration",
        "limit": 25,
    }
    if q:
        params["q"] = q
    headers = {"X-Tenant-Id": tenant_id}
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{base}/api/v1/documents/search", params=params, headers=headers)
            resp.raise_for_status()
            payload = resp.json()
            return payload if isinstance(payload, list) else []
    except Exception:
        logger.exception("ingestion search failed tenant=%s", tenant_id)
        return []
