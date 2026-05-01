"""
Shared FastAPI dependencies.

INTENTIONAL RBAC WEAKNESS: admin verification is flawed — suitable only for demos.
"""

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
