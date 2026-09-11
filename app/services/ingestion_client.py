"""Client for the doc-ingestion service (workshop cross-service contract)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def search_documents_by_class(
    *,
    tenant_id: str,
    doc_class: str,
) -> list[dict[str, Any]]:
    """Return metadata rows tagged with a closing document class."""
    settings = get_settings()
    base = settings.ingestion_service_url.rstrip("/")
    params: dict[str, str | int] = {
        "doc_class": doc_class,
        "limit": 25,
    }
    headers = {"X-Tenant-Id": tenant_id}
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{base}/api/v1/documents/search", params=params, headers=headers)
            resp.raise_for_status()
            payload = resp.json()
            return payload if isinstance(payload, list) else []
    except Exception:
        logger.exception("ingestion doc_class search failed tenant=%s class=%s", tenant_id, doc_class)
        return []
