"""Tests for the ``app.toolkit.net`` module."""

from app.toolkit.net import build_query


def test_build_query_basic():
    """Typical usage: skips ``None`` and URL‑encodes values."""
    params = {"a": 1, "b": None, "c": "hello world"}
    result = build_query(params)
    assert result == "a=1&c=hello+world"


def test_build_query_all_none_or_empty():
    """Edge cases: empty dict or all ``None`` values produce an empty string."""
    assert build_query({}) == ""
    assert build_query({"x": None, "y": None}) == ""
