"""
Partner webhook ingestion.

HMAC / signature verification is out of scope.
Client-supplied target_state is never applied. Unsigned callbacks cannot
advance signing, funding, or closure; those states stay checklist-gated.
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

_EVENT_TRANSITIONS: dict[str, tuple[str, str]] = {
    "documents_packaged": (WorkflowState.DRAFT.value, WorkflowState.DOCS_READY.value),
    "borrower_acknowledged": (
        WorkflowState.DOCS_READY.value,
        WorkflowState.BORROWER_REVIEW.value,
    ),
}


def partner_driven_next_state(
    event_type: str, current_state: str, target_state: str | None
) -> str | None:
    """Map known LOS event types only. Ignore caller-supplied target_state."""
    allowed = _EVENT_TRANSITIONS.get(event_type)
    if allowed is None:
        return None
    from_state, to_state = allowed
    if current_state != from_state:
        return None
    return to_state


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

    requested = body.get("target_state")
    if isinstance(requested, str) and requested:
        logger.warning(
            "Ignoring partner target_state=%s partner_id=%s event_type=%s",
            requested,
            partner_id,
            event_type,
        )

    next_state = partner_driven_next_state(event_type, closing.state, requested)
    if next_state is not None:
        try:
            await apply_transition(
                db,
                closing,
                next_state,
                actor_type=ActorType.PARTNER_WEBHOOK,
                actor_id=partner_id,
                payload={"event_type": event_type},
                correlation_id=body.get("idempotency_key"),
            )
        except ValueError as exc:
            row.processing_error = str(exc)
            await db.flush()
            return row

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
