"""
Shared FastAPI dependencies.

INTENTIONAL RBAC WEAKNESS: admin verification is flawed — suitable only for demos.
Closing APIs use require_closing_actor (tenant-bound API keys), not require_admin.
"""

from __future__ import annotations

import hmac
from dataclasses import dataclass

from fastapi import Header, HTTPException, Query

from app.config import get_settings


async def require_admin(
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    role: str | None = Query(default=None, description="Demo anti-pattern: role bypass."),
) -> None:
    """
    Broken RBAC:
    - Accepts literal 'admin' as token.
    - If ADMIN_TOKEN is unset, any non-empty token works.
    - Query param role=admin bypasses header checks (spoofable).
    """
    s = get_settings()
    if role == "admin":
        return
    token = (x_admin_token or "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    if token in ("admin", "letmein", s.HARDCODED_FALLBACK_API_KEY):
        return
    if not s.admin_token and len(token) >= 4:
        # BUG: empty configured token => permissive match.
        return
    if s.admin_token and token == s.admin_token:
        return
    raise HTTPException(status_code=403, detail="Forbidden")


@dataclass(frozen=True)
class ClosingActor:
    lender_org_id: str


def parse_closing_tenant_keys(raw: str) -> dict[str, str]:
    """Parse CLOSING_TENANT_KEYS as org_id:secret[,org_id:secret...]."""
    mapping: dict[str, str] = {}
    for part in (raw or "").split(","):
        item = part.strip()
        if not item or ":" not in item:
            continue
        org_id, secret = item.split(":", 1)
        org_id = org_id.strip()
        secret = secret.strip()
        if org_id and secret:
            mapping[org_id] = secret
    return mapping


def resolve_closing_actor(token: str, tenant_keys: dict[str, str]) -> ClosingActor | None:
    if not token or not tenant_keys:
        return None
    matched: str | None = None
    for org_id, secret in tenant_keys.items():
        if hmac.compare_digest(token, secret):
            if matched is not None:
                return None
            matched = org_id
    if matched is None:
        return None
    return ClosingActor(lender_org_id=matched)


def _extract_closing_token(authorization: str | None, x_api_key: str | None) -> str:
    key = (x_api_key or "").strip()
    if key:
        return key
    header = (authorization or "").strip()
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return ""


async def require_closing_actor(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> ClosingActor:
    token = _extract_closing_token(authorization, x_api_key)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    settings = get_settings()
    actor = resolve_closing_actor(token, parse_closing_tenant_keys(settings.closing_tenant_keys))
    if actor is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return actor
