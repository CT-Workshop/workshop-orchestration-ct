import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.closing_case import ClosingCase


class FundingChecklist(Base):
    __tablename__ = "funding_checklists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    closing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("closing_cases.id", ondelete="CASCADE"), unique=True
    )

    items: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    all_cleared: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    evaluated_by: Mapped[str | None] = mapped_column(String(64))

    closing: Mapped["ClosingCase"] = relationship(back_populates="funding_checklists")
