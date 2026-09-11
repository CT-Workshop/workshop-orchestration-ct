"""Same-day wire cutoff overlay.

Decision: hold is not a WorkflowState. See docs/adr/0001-same-day-wire-cutoff.md.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.wire_hold import WireHold
from app.services.timezone_clock import local_now
from app.services.workflow_engine import get_closing_or_404

REASON_PAST_CUTOFF = "past_same_day_cutoff"


def is_past_cutoff(
    *,
    tz_name: str,
    cutoff_hour: int,
    now: datetime | None = None,
) -> bool:
    local = local_now(tz_name, now=now)
    return local.hour >= cutoff_hour


async def active_hold(db: AsyncSession, closing_id: uuid.UUID) -> WireHold | None:
    result = await db.execute(
        select(WireHold).where(WireHold.closing_id == closing_id, WireHold.active.is_(True))
    )
    return result.scalar_one_or_none()


async def ensure_cutoff_hold(
    db: AsyncSession,
    closing_id: uuid.UUID,
    *,
    now: datetime | None = None,
) -> WireHold | None:
    settings = get_settings()
    if not is_past_cutoff(
        tz_name=settings.wire_cutoff_tz,
        cutoff_hour=settings.wire_cutoff_hour,
        now=now,
    ):
        return await active_hold(db, closing_id)

    existing = await active_hold(db, closing_id)
    if existing:
        return existing

    local = local_now(settings.wire_cutoff_tz, now=now)
    hold = WireHold(
        closing_id=closing_id,
        reason=REASON_PAST_CUTOFF,
        detail=(
            f"Same-day wire window closed at {settings.wire_cutoff_hour:02d}:00 "
            f"{settings.wire_cutoff_tz} (local {local.isoformat()})"
        ),
        active=True,
    )
    db.add(hold)
    await db.flush()
    return hold


async def release_hold(
    db: AsyncSession,
    closing_id: uuid.UUID,
    *,
    released_by: str,
) -> WireHold:
    closing = await get_closing_or_404(db, closing_id)
    if closing is None:
        raise LookupError("closing not found")
    hold = await active_hold(db, closing_id)
    if hold is None:
        raise LookupError("no active wire hold")
    hold.active = False
    hold.released_at = datetime.utcnow()
    hold.released_by = released_by
    await db.flush()
    return hold


async def wire_window_payload(
    db: AsyncSession,
    closing_id: uuid.UUID,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    local = local_now(settings.wire_cutoff_tz, now=now)
    hold = await active_hold(db, closing_id)
    past = is_past_cutoff(
        tz_name=settings.wire_cutoff_tz,
        cutoff_hour=settings.wire_cutoff_hour,
        now=now,
    )
    return {
        "timezone": settings.wire_cutoff_tz,
        "cutoff_hour": settings.wire_cutoff_hour,
        "local_time": local.isoformat(),
        "past_cutoff": past,
        "can_auto_close": not past and hold is None,
        "active_hold": (
            {
                "id": str(hold.id),
                "reason": hold.reason,
                "detail": hold.detail,
            }
            if hold
            else None
        ),
    }
