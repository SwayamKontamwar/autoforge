"""Tests for configuration helpers in ``app.toolkit.config``."""

from __future__ import annotations

import pytest

from app.toolkit import get_env_bool


@pytest.mark.parametrize(
    "value,expected",
    [
        ("true", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("Y", True),
        ("on", True),
        ("false", False),
        ("FALSE", False),
        ("0", False),
        ("no", False),
        ("N", False),
        ("off", False),
    ],
)
def test_get_env_bool_recognises_truthy_and_falsy(monkeypatch, value, expected):
    """The function should correctly interpret common boolean strings."""
    monkeypatch.setenv("TEST_BOOL", value)
    assert get_env_bool("TEST_BOOL") is expected


def test_get_env_bool_default_when_unset(monkeypatch):
    """When the variable is not present, the supplied default is returned."""
    monkeypatch.delenv("TEST_BOOL", raising=False)
    assert get_env_bool("TEST_BOOL", default=True) is True
    assert get_env_bool("TEST_BOOL", default=False) is False


def test_get_env_bool_raises_on_invalid_value(monkeypatch):
    """A non‑recognised value should raise ``ValueError``."""
    monkeypatch.setenv("TEST_BOOL", "maybe")
    with pytest.raises(ValueError):
        get_env_bool("TEST_BOOL")
