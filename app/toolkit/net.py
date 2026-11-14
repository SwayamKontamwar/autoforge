"""Network‑related utility helpers.

This module provides helpers for building query strings, joining URLs,
stripping query components, and removing specific query parameters.
"""

from __future__ import annotations

from typing import Any, Mapping, Tuple
from urllib.parse import (
    parse_qsl,
    quote_plus,
    urlencode,
    urlparse,
    urlunparse,
)


def build_query(params: Mapping[str, Any]) -> str:
    """Convert a mapping of query parameters into a URL‑encoded query string.

    Parameters whose value is ``None`` are omitted. The order of parameters
    follows the insertion order of the input mapping.
    """
    parts: list[str] = []
    for key, value in params.items():
        if value is None:
            continue
        encoded_key = quote_plus(str(key))
        encoded_value = quote_plus(str(value))
        parts.append(f"{encoded_key}={encoded_value}")
    return "&".join(parts)


def join_url(base: str, rel: str) -> str:
    """Join a base URL and a relative URL/path.

    - If ``rel`` is an absolute URL (has a scheme), it overrides ``base``.
    - Empty ``rel`` returns ``base`` unchanged.
    - Otherwise, exactly one ``/`` is placed between the parts.
    """
    if not rel:
        return base
    rel_parsed = urlparse(rel)
    if rel_parsed.scheme:
        return rel
    # Ensure single slash between base and rel
    return f"{base.rstrip('/')}/{rel.lstrip('/')}"


def strip_query(url: str) -> str:
    """Return ``url`` without its query component, preserving fragments."""
    parsed = urlparse(url)
    stripped = parsed._replace(query="")
    return urlunparse(stripped)


def remove_query_param(url: str, param: str) -> str:
    """Return ``url`` with all occurrences of ``param`` removed from its query.

    The order of remaining parameters is preserved. If the removal results in
    an empty query string, the ``?`` is omitted. Fragments are preserved.
    """
    parsed = urlparse(url)
    # Parse query preserving order and blank values
    query_items: list[Tuple[str, str]] = parse_qsl(parsed.query, keep_blank_values=True)
    # Filter out the unwanted parameter
    filtered_items = [(k, v) for k, v in query_items if k != param]
    # Re‑encode the filtered query
    new_query = urlencode(filtered_items, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    return urlunparse(new_parsed)
