from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import PartnerWebhookEvent
from app.schemas.partner import PartnerWebhookIn
from app.schemas.webhook_replay import PartnerWebhookReceipt
from app.services import partner_webhook_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/partner")
async def partner_webhook(
    body: PartnerWebhookIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> PartnerWebhookReceipt:
    """
    Accept unsigned partner callbacks.

    INTENTIONALLY INSECURE: no signature verification.
    Replays with the same idempotency key do not mutate workflow again.
    """
    settings = get_settings()
    if settings.partner_idempotency_required and not (body.idempotency_key or "").strip():
        raise HTTPException(
            status_code=400,
            detail="idempotency_key is required for partner webhook deliveries",
        )

    headers_snapshot = {k: v for k, v in request.headers.items()}
    envelope = body.model_dump()

    existing = None
    key = (body.idempotency_key or "").strip()
    if key:
        from app.services.partner_idempotency import find_existing_delivery

        existing = await find_existing_delivery(
            db, partner_id=body.partner_id, idempotency_key=key
        )

    row = await partner_webhook_service.ingest_partner_event(
        db,
        partner_id=body.partner_id,
        event_type=body.event_type,
        body=envelope,
        headers_snapshot=headers_snapshot,
    )
    replayed = existing is not None and row.id == existing.id
    if not replayed:
        await db.commit()

    # Queue downstream funding evaluation when relevant LOS signals arrive.
    # Replays must not enqueue a second funding evaluate.
    if body.closing_id and not replayed:
        try:
            uuid.UUID(str(body.closing_id))
        except ValueError:
            pass
        else:
            from app.tasks.jobs import evaluate_funding_task

            evaluate_funding_task.delay(str(body.closing_id))

    return PartnerWebhookReceipt(
        received=True,
        replayed=replayed,
        stored_event_id=str(row.id),
        processed_ok=row.processed_ok,
        error=row.processing_error,
    )


@router.get("/partner/{event_id}")
async def get_partner_event(
    event_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    result = await db.execute(
        select(PartnerWebhookEvent).where(PartnerWebhookEvent.id == event_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Webhook event not found")
    return {
        "id": str(row.id),
        "partner_id": row.partner_id,
        "event_type": row.event_type,
        "idempotency_key": row.idempotency_key,
        "processed_ok": row.processed_ok,
        "error": row.processing_error,
        "received_at": row.received_at.isoformat() if row.received_at else None,
    }
