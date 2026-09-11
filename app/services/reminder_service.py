"""
Reminder orchestration — enqueue-only in API; delivery happens in workers.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.workflow_engine import get_closing_or_404

logger = logging.getLogger(__name__)


async def schedule_reminders(
    db: AsyncSession,
    closing_id: uuid.UUID,
    *,
    channel: str,
    template: str,
    schedule_in_seconds: int,
) -> dict:
    closing = await get_closing_or_404(db, closing_id)
    if closing is None:
        raise LookupError("closing not found")

    # After cutoff, default to the next-day wire template so title is not told "funded today".
    from app.services import wire_cutoff

    if template == "closing_reminder_v1":
        try:
            window = await wire_cutoff.wire_window_payload(db, closing_id)
        except ValueError:
            window = {}
        if window.get("past_cutoff"):
            template = "wire_cutoff_next_day_v1"

    # Lazy import avoids circular import at module load in tests.
    from app.tasks.jobs import send_reminder_task

    async_result = send_reminder_task.apply_async(
        args=[str(closing_id), channel, template],
        countdown=schedule_in_seconds,
    )
    logger.info(
        "queued reminder closing=%s task_id=%s",
        closing_id,
        async_result.id,
    )
    return {
        "queued": True,
        "task_id": async_result.id,
        "channel": channel,
        "template": template,
        "countdown_seconds": schedule_in_seconds,
    }
