from typing import Any

from pydantic import BaseModel, Field


class PartnerWebhookIn(BaseModel):
    """
    Inbound payload — intentionally permissive (unsigned / replay-friendly).
    """

    partner_id: str = Field(..., min_length=1, max_length=64)
    event_type: str = Field(..., min_length=1, max_length=64)
    external_ref: str | None = None
    closing_id: str | None = None
    target_state: str | None = Field(
        default=None,
        description="Optional workflow transition hint.",
    )
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(
        default=None,
        description="Required when PARTNER_IDEMPOTENCY_REQUIRED=true. Replays return the first event.",
    )
