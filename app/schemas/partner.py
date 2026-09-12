from typing import Any

from pydantic import BaseModel, Field


class PartnerWebhookIn(BaseModel):
    """
    Inbound partner callback.

    target_state is accepted for compatibility and persisted on the event
    row; ingest never applies it as a workflow transition.
    """

    partner_id: str = Field(..., min_length=1, max_length=64)
    event_type: str = Field(..., min_length=1, max_length=64)
    external_ref: str | None = None
    closing_id: str | None = None
    target_state: str | None = Field(
        default=None,
        description="Ignored for transitions; signing/funding/closure stay checklist-gated.",
    )
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(
        default=None,
        description="Stored but not enforced for duplicates (replay scenario).",
    )
