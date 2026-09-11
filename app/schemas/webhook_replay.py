from typing import Any

from pydantic import BaseModel


class PartnerWebhookReceipt(BaseModel):
    received: bool
    replayed: bool
    stored_event_id: str
    processed_ok: bool | None = None
    error: str | None = None
    extra: dict[str, Any] | None = None
