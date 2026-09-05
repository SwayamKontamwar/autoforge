"""Network‑related utility helpers.

This module currently provides a single helper, ``build_query``, which converts a
mapping of query parameters into a URL‑encoded query string, omitting any
parameters whose value is ``None``. The order of parameters in the resulting
string follows the insertion order of the input mapping.
"""

from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import quote_plus, urlparse, urlunparse


def build_query(params: Mapping[str, Any]) -> str:
    """Return a URL‑encoded query string built from *params*.

    ``None`` values are omitted from the output. All keys and values are
    converted to strings and URL‑escaped using :func:`urllib.parse.quote_plus`.

    Args:
        params: Mapping of query parameter names to values.

    Returns:
        A query string (e.g. ``"a=1&b=hello+world"``). An empty string is
        returned when *params* is empty or contains only ``None`` values.
    """
    parts: list[str] = []
    for key, value in params.items():
        if value is None:
            continue
        encoded_key = quote_plus(str(key))
        encoded_value = quote_plus(str(value))
        parts.append(f"{encoded_key}={encoded_value}")
    return "&".join(parts)


def join_url(base: str, relative: str) -> str:
    """Safely join *base* URL with *relative* path.

    The function ensures exactly one ``/`` between the two parts, removes
    duplicate slashes, and returns *relative* unchanged if it is an absolute
    URL (i.e. contains a scheme). Empty *base* or *relative* values are handled
    gracefully.

    Args:
        base: The base URL (e.g. ``"http://example.com/api"``).
        relative: The relative path to append (e.g. ``"users"``).

    Returns:
        The combined URL.
    """
    if not base:
        return relative
    if not relative:
        return base
    # If the relative URL is absolute (has a scheme), return it unchanged.
    if urlparse(relative).scheme:
        return relative
    # Remove trailing slash from base and leading slash from relative to avoid
    # duplicate slashes.
    base_stripped = base.rstrip("/")
    rel_stripped = relative.lstrip("/")
    return f"{base_stripped}/{rel_stripped}"


def strip_query(url: str) -> str:
    """Return *url* without its query component.

    The function preserves the scheme, netloc, path, params, and fragment.
    If *url* has no query part, it is returned unchanged.

    Args:
        url: The URL string to process.

    Returns:
        The URL without the query string.
    """
    parsed = urlparse(url)
    if not parsed.query:
        return url
    # Rebuild the URL with an empty query component.
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            "",
            parsed.fragment,
        )
    )
