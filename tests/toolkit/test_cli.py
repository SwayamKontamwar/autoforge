"""Tests for the simple CLI argument parser."""

import pytest

from app.toolkit import parse_args_simple


def test_parse_args_simple_basic() -> None:
    args = ["--host", "localhost", "--port", "8080"]
    expected = {"host": "localhost", "port": "8080"}
    assert parse_args_simple(args) == expected


def test_parse_args_simple_missing_value_raises() -> None:
    with pytest.raises(ValueError) as exc:
        parse_args_simple(["--onlykey"])
    assert "Missing value for option '--onlykey'" in str(exc.value)
