"""Tests for configuration helpers in ``app.toolkit.config``."""

from __future__ import annotations

import pytest

from app.toolkit import get_env_bool, get_env_int, get_env_list


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


def test_get_env_int_parses_valid_integer(monkeypatch):
    """Valid integer strings should be parsed correctly."""
    monkeypatch.setenv("TEST_INT", "42")
    assert get_env_int("TEST_INT") == 42


def test_get_env_int_default_when_unset(monkeypatch):
    """When the variable is missing, the default integer is returned."""
    monkeypatch.delenv("TEST_INT", raising=False)
    assert get_env_int("TEST_INT", default=7) == 7


def test_get_env_int_raises_on_invalid_value(monkeypatch):
    """Non‑integer values should raise ``ValueError``."""
    monkeypatch.setenv("TEST_INT", "not-an-int")
    with pytest.raises(ValueError):
        get_env_int("TEST_INT")


def test_get_env_list_parses_comma_separated(monkeypatch):
    """A comma‑separated string should be split into a list of stripped items."""
    monkeypatch.setenv("TEST_LIST", "a, b ,c ,  d")
    assert get_env_list("TEST_LIST") == ["a", "b", "c", "d"]


def test_get_env_list_default_when_unset(monkeypatch):
    """When the variable is missing, the default (or empty list) is returned."""
    monkeypatch.delenv("TEST_LIST", raising=False)
    assert get_env_list("TEST_LIST") == []
    assert get_env_list("TEST_LIST", default=["x", "y"]) == ["x", "y"]


def test_get_env_list_ignores_empty_entries(monkeypatch):
    """Consecutive commas or leading/trailing commas should not produce empty items."""
    monkeypatch.setenv("TEST_LIST", ",,a,, ,b,,")
    assert get_env_list("TEST_LIST") == ["a", "b"]
