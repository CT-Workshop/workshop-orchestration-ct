from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.partner import PartnerWebhookIn
from app.services import partner_webhook_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/partner")
async def partner_webhook(
    body: PartnerWebhookIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Accept partner callbacks.

    Duplicate (partner_id, idempotency_key) deliveries return the original event.
    Client-supplied target_state is stored but never applied.
    """
    headers_snapshot = {k: v for k, v in request.headers.items()}
    envelope = body.model_dump()

    row, replayed = await partner_webhook_service.ingest_partner_event(
        db,
        partner_id=body.partner_id,
        event_type=body.event_type,
        body=envelope,
        headers_snapshot=headers_snapshot,
    )
    await db.commit()

    queued = False
    # First delivery only — retries must not enqueue a second funding evaluation.
    if not replayed and body.closing_id:
        try:
            uuid.UUID(str(body.closing_id))
        except ValueError:
            pass
        else:
            from app.tasks.enqueue import enqueue_after_commit
            from app.tasks.jobs import evaluate_funding_task

            queued = enqueue_after_commit(evaluate_funding_task, str(body.closing_id))

    return {
        "received": True,
        "stored_event_id": str(row.id),
        "replayed": replayed,
        "queued": queued,
        "processed_ok": row.processed_ok,
        "error": row.processing_error,
    }
