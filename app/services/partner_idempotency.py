"""Lookup helper for partner webhook deliveries.

Decision: uniqueness is (partner_id, idempotency_key). See ADR 0002.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PartnerWebhookEvent


async def find_existing_delivery(
    db: AsyncSession,
    *,
    partner_id: str,
    idempotency_key: str,
) -> PartnerWebhookEvent | None:
    result = await db.execute(
        select(PartnerWebhookEvent).where(
            PartnerWebhookEvent.partner_id == partner_id,
            PartnerWebhookEvent.idempotency_key == idempotency_key,
        )
    )
    return result.scalars().first()
