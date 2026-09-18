"""Tests for the ``humanize_delta`` function in ``app.toolkit.datetimes``."""

from datetime import timedelta

from app.toolkit import humanize_delta


def test_humanize_delta_past_hours():
    """A positive timedelta should be expressed with an ``ago`` suffix."""
    delta = timedelta(hours=3, minutes=15)
    assert humanize_delta(delta) == "3 hours ago"


def test_humanize_delta_future_minutes():
    """A negative timedelta should be expressed with an ``in`` prefix."""
    delta = timedelta(minutes=-5, seconds=-30)
    assert humanize_delta(delta) == "in 5 minutes"


def test_humanize_delta_zero():
    """A zero timedelta should return a friendly phrase."""
    delta = timedelta(0)
    assert humanize_delta(delta) == "just now"
