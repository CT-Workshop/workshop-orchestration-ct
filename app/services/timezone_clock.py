"""Clock helpers for title-company local time. UTC is never the cutoff source."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def local_now(tz_name: str, *, now: datetime | None = None) -> datetime:
    """Return `now` in `tz_name`. Naive datetimes are treated as UTC."""
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown timezone {tz_name!r}") from exc
    stamp = now or datetime.utcnow()
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=ZoneInfo("UTC"))
    return stamp.astimezone(tz)
