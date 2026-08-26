"""Utility functions for data serialization.

Currently provides JSON Lines (JSONL) conversion for iterables of objects.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, List


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


def from_jsonl(text: str) -> List[Any]:
    """Parse JSON Lines (JSONL) text into a list of objects.

    Empty lines (including lines containing only whitespace) are ignored.
    The function tolerates a trailing newline. If any non‑empty line is not
    valid JSON, a ``json.JSONDecodeError`` is raised.

    Args:
        text: A string containing JSON objects separated by newlines.

    Returns:
        A list of deserialized Python objects.

    Raises:
        json.JSONDecodeError: If a non‑empty line cannot be parsed as JSON.
    """
    if not text:
        return []
    result: List[Any] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        result.append(json.loads(stripped))
    return result
