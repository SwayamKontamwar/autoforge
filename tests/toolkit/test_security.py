import re

import pytest

from app.toolkit.security import constant_time_equals, generate_token


def test_constant_time_equals_identical_strings() -> None:
    assert constant_time_equals("secure-token-123", "secure-token-123") is True


def test_constant_time_equals_different_strings() -> None:
    assert constant_time_equals("secure-token-123", "secure-token-124") is False


def test_constant_time_equals_length_mismatch() -> None:
    assert constant_time_equals("short", "much longer string") is False


def test_constant_time_equals_empty_strings() -> None:
    assert constant_time_equals("", "") is True


def test_generate_token_is_urlsafe_and_correct_length() -> None:
    token = generate_token(16)
    assert isinstance(token, str)
    # URL‑safe characters only (alphanumeric, hyphen, underscore)
    assert re.fullmatch(r"[A-Za-z0-9_-]+", token)
    # token_urlsafe expands 16 bytes to at least 22 characters
    assert len(token) >= 22


def test_generate_token_invalid_length_raises() -> None:
    with pytest.raises(ValueError):
        generate_token(0)
