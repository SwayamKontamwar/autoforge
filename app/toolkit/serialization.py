"""Utility functions for data serialization.

Currently provides JSON Lines (JSONL) conversion for iterables of objects.
"""

from __future__ import annotations

import json
from typing import Any, Iterable


def to_jsonl(items: Iterable[Any]) -> str:
    """Serialise an iterable of objects to JSON Lines (JSONL) format.

    Each object is JSON‑encoded on its own line. The returned string does not
    end with a trailing newline; an empty iterable yields ``""``.

    Args:
        items: An iterable of JSON‑serialisable objects.

    Returns:
        A string containing one JSON object per line.

    Raises:
        TypeError: If any element of *items* cannot be JSON‑encoded.
    """
    lines = [json.dumps(item, ensure_ascii=False) for item in items]
    return "\n".join(lines)
