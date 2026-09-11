from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.wire_cutoff import is_past_cutoff


def test_before_cutoff_eastern():
    noon = datetime(2026, 9, 11, 16, 0, tzinfo=ZoneInfo("UTC"))  # 12:00 ET
    assert is_past_cutoff(tz_name="America/New_York", cutoff_hour=15, now=noon) is False


def test_after_cutoff_eastern():
    evening = datetime(2026, 9, 11, 20, 0, tzinfo=ZoneInfo("UTC"))  # 16:00 ET
    assert is_past_cutoff(tz_name="America/New_York", cutoff_hour=15, now=evening) is True
