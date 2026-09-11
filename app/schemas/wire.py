from typing import Any

from pydantic import BaseModel, Field


class WireWindowResponse(BaseModel):
    timezone: str
    cutoff_hour: int
    local_time: str
    past_cutoff: bool
    can_auto_close: bool
    active_hold: dict[str, Any] | None = None


class WireHoldReleaseRequest(BaseModel):
    released_by: str = Field(..., min_length=1, max_length=64)
    note: str | None = Field(default=None, max_length=512)
