"""Tests for the ``now_utc`` function in the datetimes toolkit."""

from datetime import datetime, timezone

from app.toolkit import now_utc


def test_now_utc_is_timezone_aware_and_utc():
    """now_utc should return a timezone‑aware datetime in UTC."""
    dt = now_utc()
    assert isinstance(dt, datetime)
    assert dt.tzinfo is timezone.utc


def test_now_utc_is_recent():
    """The returned datetime should be between two successive UTC timestamps."""
    before = datetime.now(timezone.utc)
    dt = now_utc()
    after = datetime.now(timezone.utc)
    assert before <= dt <= after
