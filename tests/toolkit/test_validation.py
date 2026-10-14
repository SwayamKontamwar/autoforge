"""Tests for validation utilities."""

from app.toolkit import is_email, is_ipv6, is_url, is_uuid


def test_is_email_valid():
    assert is_email("user@example.com")


def test_is_email_invalid():
    assert not is_email("not-an-email")


def test_is_url_valid():
    assert is_url("https://example.com/path")


def test_is_url_invalid():
    assert not is_url("ftp://example.com")


def test_is_ipv6_valid():
    assert is_ipv6("2001:0db8:85a3:0000:0000:8a2e:0370:7334")


def test_is_ipv6_invalid():
    assert not is_ipv6("not-an-ipv6")


def test_is_uuid_valid():
    # Standard UUID format
    assert is_uuid("550e8400-e29b-41d4-a716-446655440000")


def test_is_uuid_invalid():
    # Missing hyphens should be rejected
    assert not is_uuid("550e8400e29b41d4a716446655440000")


def test_is_uuid_non_string():
    assert not is_uuid(None)
