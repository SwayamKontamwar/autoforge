"""Tests for configuration helpers in ``app.toolkit.config``."""

from __future__ import annotations

import pytest

from app.toolkit import get_env_bool, get_env_int


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


@pytest.mark.parametrize(
    "value,expected",
    [
        ("42", 42),
        ("  7  ", 7),
        ("-3", -3),
    ],
)
def test_get_env_int_parses_valid_integers(monkeypatch, value, expected):
    """Valid integer strings (including whitespace) should be parsed correctly."""
    monkeypatch.setenv("TEST_INT", value)
    assert get_env_int("TEST_INT") == expected


def test_get_env_int_default_when_unset(monkeypatch):
    """When the variable is missing, the provided default is returned."""
    monkeypatch.delenv("TEST_INT", raising=False)
    assert get_env_int("TEST_INT", default=10) == 10
    assert get_env_int("TEST_INT", default=-5) == -5


def test_get_env_int_raises_on_invalid_value(monkeypatch):
    """A non‑integer value should raise ``ValueError``."""
    monkeypatch.setenv("TEST_INT", "not-an-int")
    with pytest.raises(ValueError):
        get_env_int("TEST_INT")
