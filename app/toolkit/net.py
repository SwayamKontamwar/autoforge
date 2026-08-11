"""Network‑related utility helpers.

This module currently provides a single helper, ``build_query``, which converts a
mapping of query parameters into a URL‑encoded query string, omitting any
parameters whose value is ``None``. The order of parameters in the resulting
string follows the insertion order of the input mapping.
"""

from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import quote_plus


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
