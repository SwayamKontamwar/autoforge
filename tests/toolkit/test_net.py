"""Tests for the ``app.toolkit.net`` module."""

from app.toolkit.net import build_query, join_url, strip_query


def test_build_query_basic():
    """Typical usage: skips ``None`` and URL‑encodes values."""
    params = {"a": 1, "b": None, "c": "hello world"}
    result = build_query(params)
    assert result == "a=1&c=hello+world"


def test_build_query_all_none_or_empty():
    """Edge cases: empty dict or all ``None`` values produce an empty string."""
    assert build_query({}) == ""
    assert build_query({"x": None, "y": None}) == ""


def test_join_url_basic():
    """Joining with proper slashes should concatenate correctly."""
    base = "http://example.com/api/"
    rel = "users"
    assert join_url(base, rel) == "http://example.com/api/users"


def test_join_url_edge_cases():
    """Handles missing/extra slashes, empty parts, and absolute URLs."""
    # Base without trailing slash, relative with leading slash
    assert join_url("http://example.com/api", "/users") == "http://example.com/api/users"
    # Empty relative returns base unchanged
    assert join_url("http://example.com/api/", "") == "http://example.com/api/"
    # Absolute relative overrides base
    assert join_url("http://example.com/api", "https://other.com/path") == "https://other.com/path"


def test_strip_query_basic():
    """Removing a standard query string."""
    url = "https://example.com/path?foo=bar&baz=qux"
    assert strip_query(url) == "https://example.com/path"


def test_strip_query_edge_cases():
    """No query returns unchanged; fragment is preserved."""
    # No query
    assert strip_query("https://example.com/path") == "https://example.com/path"
    # Query with fragment
    url = "https://example.com/path?foo=bar#section"
    assert strip_query(url) == "https://example.com/path#section"
