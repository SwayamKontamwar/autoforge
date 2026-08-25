"""Tests for the confirm_prompt utility."""

import pytest

from app.toolkit import confirm_prompt


def test_confirm_prompt_with_default_and_empty_input(monkeypatch):
    # Default True, empty input should return True
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert confirm_prompt("Proceed? ", default=True) is True

    # Default False, empty input should return False
    monkeypatch.setattr("builtins.input", lambda _: "")
    assert confirm_prompt("Proceed? ", default=False) is False


def test_confirm_prompt_explicit_and_invalid_inputs(monkeypatch):
    # Explicit affirmative input
    monkeypatch.setattr("builtins.input", lambda _: "YeS")
    assert confirm_prompt("Proceed? ") is True

    # Explicit negative input
    monkeypatch.setattr("builtins.input", lambda _: "n")
    assert confirm_prompt("Proceed? ") is False

    # Empty input without default raises ValueError
    monkeypatch.setattr("builtins.input", lambda _: "")
    with pytest.raises(ValueError):
        confirm_prompt("Proceed? ")

    # Unrecognised input raises ValueError
    monkeypatch.setattr("builtins.input", lambda _: "maybe")
    with pytest.raises(ValueError):
        confirm_prompt("Proceed? ")
