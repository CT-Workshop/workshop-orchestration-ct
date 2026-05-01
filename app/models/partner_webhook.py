import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PartnerWebhookEvent(Base):
    """
    Inbound partner events.

    INTENTIONAL WEAKNESS: no signature / replay columns enforced at write time.
    """

    __tablename__ = "partner_webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    partner_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), index=True)

    raw_body: Mapped[dict[str, Any]] = mapped_column(JSONB)
    headers_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    processed_ok: Mapped[bool] = mapped_column(default=False)
    processing_error: Mapped[str | None] = mapped_column(Text)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )
