from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClosingCase, NotaryAssignment, WorkflowState
from app.models.enums import ActorType, NotaryAssignmentStatus
from app.services.workflow_engine import apply_transition, get_closing_or_404


async def _existing_assignment(
    db: AsyncSession, closing_id: uuid.UUID, notary_id: str
) -> NotaryAssignment | None:
    q = await db.execute(
        select(NotaryAssignment).where(
            NotaryAssignment.closing_id == closing_id,
            NotaryAssignment.notary_id == notary_id,
        )
    )
    return q.scalar_one_or_none()


async def assign_notary(
    db: AsyncSession,
    closing_id: uuid.UUID,
    notary_id: str,
    signing_agency_id: str | None,
    actor_id: str | None,
) -> tuple[NotaryAssignment, bool]:
    closing = await get_closing_or_404(db, closing_id)
    if closing is None:
        raise LookupError("closing not found")

    existing = await _existing_assignment(db, closing.id, notary_id)
    if existing is not None:
        return existing, True

    row = NotaryAssignment(
        closing_id=closing.id,
        notary_id=notary_id,
        signing_agency_id=signing_agency_id,
        status=NotaryAssignmentStatus.INVITED.value,
    )
    db.add(row)

    # Advance workflow toward signing when assignment lands.
    if closing.state in (
        WorkflowState.DRAFT.value,
        WorkflowState.DOCS_READY.value,
        WorkflowState.BORROWER_REVIEW.value,
    ):
        await apply_transition(
            db,
            closing,
            WorkflowState.SIGNING_SCHEDULED.value,
            actor_type=ActorType.NOTARY,
            actor_id=actor_id or notary_id,
            payload={"signing_agency_id": signing_agency_id},
        )
    elif closing.state == WorkflowState.SIGNING_SCHEDULED.value:
        pass
    else:
        # Still record assignment; state unchanged (operator override scenario).
        pass

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raced = await _existing_assignment(db, closing_id, notary_id)
        if raced is not None:
            return raced, True
        raise
    return row, False


async def mark_signing_completed(db: AsyncSession, closing_id: uuid.UUID) -> ClosingCase | None:
    closing = await get_closing_or_404(db, closing_id)
    if closing is None:
        return None
    now = datetime.utcnow()
    if closing.state != WorkflowState.SIGNED.value:
        await apply_transition(
            db,
            closing,
            WorkflowState.SIGNED.value,
            actor_type=ActorType.SYSTEM,
            actor_id="notary_service",
            payload={"completed_at": now.isoformat()},
        )
    return closing
