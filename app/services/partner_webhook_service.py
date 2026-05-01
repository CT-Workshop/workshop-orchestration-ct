"""
Partner webhook ingestion.

INTENTIONAL WEAKNESSES:
- No HMAC / signature verification on ingest.
- idempotency_key is persisted but duplicates are not rejected (replay).
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClosingCase, PartnerWebhookEvent, WorkflowState
from app.models.enums import ActorType
from app.services.workflow_engine import apply_transition, get_closing_or_404

logger = logging.getLogger(__name__)


async def ingest_partner_event(
    db: AsyncSession,
    *,
    partner_id: str,
    event_type: str,
    body: dict[str, Any],
    headers_snapshot: dict[str, Any] | None,
) -> PartnerWebhookEvent:
    # DEMO: always accept — no signature gate.
    row = PartnerWebhookEvent(
        partner_id=partner_id,
        event_type=event_type,
        idempotency_key=body.get("idempotency_key"),
        raw_body=body,
        headers_snapshot=headers_snapshot,
        processed_ok=False,
    )
    db.add(row)
    await db.flush()

    closing = await _resolve_closing(db, body)
    if closing is None:
        row.processing_error = "closing_not_resolved"
        await db.flush()
        return row

    target = body.get("target_state")
    if isinstance(target, str) and target:
        try:
            await apply_transition(
                db,
                closing,
                target,
                actor_type=ActorType.PARTNER_WEBHOOK,
                actor_id=partner_id,
                payload={"event_type": event_type, "envelope": body},
                correlation_id=body.get("idempotency_key"),
            )
        except ValueError as exc:
            row.processing_error = str(exc)
            await db.flush()
            return row

    # Convenience transitions for demo LOS events
    if event_type == "documents_packaged":
        if closing.state == WorkflowState.DRAFT.value:
            await apply_transition(
                db,
                closing,
                WorkflowState.DOCS_READY.value,
                actor_type=ActorType.PARTNER_WEBHOOK,
                actor_id=partner_id,
                payload={"event_type": event_type},
            )
    elif event_type == "borrower_acknowledged":
        if closing.state == WorkflowState.DOCS_READY.value:
            await apply_transition(
                db,
                closing,
                WorkflowState.BORROWER_REVIEW.value,
                actor_type=ActorType.PARTNER_WEBHOOK,
                actor_id=partner_id,
                payload={"event_type": event_type},
            )

    row.processed_ok = True
    await db.flush()
    return row


async def _resolve_closing(db: AsyncSession, body: dict[str, Any]) -> ClosingCase | None:
    cid = body.get("closing_id")
    if cid:
        try:
            uid = uuid.UUID(str(cid))
            return await get_closing_or_404(db, uid)
        except ValueError:
            return None

    ext = body.get("external_ref")
    if not ext:
        return None
    q = await db.execute(select(ClosingCase).where(ClosingCase.external_ref == ext))
    return q.scalar_one_or_none()
