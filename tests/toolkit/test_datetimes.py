"""Tests for the ``app.toolkit.datetimes`` module."""

from datetime import datetime, timedelta, timezone

from app.toolkit import parse_iso


def test_parse_iso_utc_z_suffix():
    """A string ending with ``Z`` should be interpreted as UTC."""
    iso_str = "2023-01-02T03:04:05Z"
    result = parse_iso(iso_str)
    assert result == datetime(2023, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    assert result.tzinfo == timezone.utc


def test_parse_iso_with_offset():
    """ISO strings containing an explicit offset must preserve that offset."""
    iso_str = "2023-01-02T03:04:05+02:00"
    result = parse_iso(iso_str)
    expected = datetime(2023, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=2)))
    assert result == expected
    assert result.tzinfo.utcoffset(result) == timedelta(hours=2)


def test_parse_iso_naive_assumed_utc():
    """A naive ISO string (no offset) should be treated as UTC."""
    iso_str = "2023-01-02T03:04:05"
    result = parse_iso(iso_str)
    assert result == datetime(2023, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    assert result.tzinfo == timezone.utc
