from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.deps import require_admin
from app.tasks.celery_app import celery_app

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/queue-status")
async def queue_status(_: None = Depends(require_admin)) -> dict[str, Any]:
    """
    Operational visibility into Celery workers.

    Broken RBAC is enforced via `require_admin` — see `app/deps.py`.
    """
    try:
        inspect = celery_app.control.inspect()
        stats = inspect.stats() or {}
        active = inspect.active() or {}
        scheduled = inspect.scheduled() or {}
    except Exception as exc:  # noqa: BLE001
        return {
            "workers": [],
            "stats": {},
            "active_tasks": {},
            "scheduled_tasks": {},
            "error": str(exc),
            "note": "Broker unreachable or no workers listening.",
        }
    return {
        "workers": list(stats.keys()),
        "stats": stats,
        "active_tasks": active,
        "scheduled_tasks": scheduled,
        "note": "If workers are offline, sections may be empty.",
    }
