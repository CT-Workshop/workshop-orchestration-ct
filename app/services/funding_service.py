from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ClosingCase, FundingChecklist, WorkflowState
from app.models.enums import ActorType
from app.services.workflow_engine import apply_transition, get_closing_or_404


DEFAULT_ITEMS: list[dict[str, Any]] = [
    {"id": "wire_instructions", "label": "Wire instructions confirmed", "done": False},
    {"id": "final_cd", "label": "Final CD acknowledged", "done": False},
    {"id": "title_policy", "label": "Title policy requirements satisfied", "done": False},
    {"id": "docs_recorded", "label": "Recorded / pending recording acceptable", "done": False},
]


async def ensure_checklist(db: AsyncSession, closing_id: uuid.UUID) -> FundingChecklist:
    result = await db.execute(
        select(FundingChecklist).where(FundingChecklist.closing_id == closing_id)
    )
    row = result.scalar_one_or_none()
    if row:
        return row
    row = FundingChecklist(closing_id=closing_id, items=list(DEFAULT_ITEMS), all_cleared=False)
    db.add(row)
    await db.flush()
    return row


async def evaluate_funding_readiness(db: AsyncSession, closing_id: uuid.UUID) -> FundingChecklist:
    closing = await get_closing_or_404(db, closing_id)
    if closing is None:
        raise LookupError("closing not found")

    chk = await ensure_checklist(db, closing_id)
    items = list(chk.items)
    all_cleared = bool(items) and all(bool(i.get("done")) for i in items)
    chk.all_cleared = all_cleared
    chk.last_evaluated_at = datetime.utcnow()
    chk.evaluated_by = "funding_service"

    if (
        all_cleared
        and closing.state == WorkflowState.SIGNED.value
    ):
        await apply_transition(
            db,
            closing,
            WorkflowState.FUNDING_READY.value,
            actor_type=ActorType.SYSTEM,
            actor_id="funding_service",
            payload={"checklist_id": str(chk.id)},
        )
    elif all_cleared and closing.state == WorkflowState.FUNDING_READY.value:
        await apply_transition(
            db,
            closing,
            WorkflowState.CLOSED.value,
            actor_type=ActorType.SYSTEM,
            actor_id="funding_service",
            payload={"checklist_id": str(chk.id)},
        )

    await db.flush()
    return chk


async def patch_checklist_items(
    db: AsyncSession,
    closing_id: uuid.UUID,
    items: list[dict[str, Any]],
) -> FundingChecklist:
    chk = await ensure_checklist(db, closing_id)
    chk.items = items
    await db.flush()
    return chk
