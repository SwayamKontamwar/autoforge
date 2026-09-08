"""Utility functions for data serialization.

Currently provides JSON Lines (JSONL) conversion for iterables of objects.
"""

from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
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


def dataclass_to_dict(obj: Any) -> Any:
    """Recursively convert a dataclass instance (or structures containing it) to a dict.

    Handles nested dataclasses, lists, tuples, sets and dictionaries. Primitive
    types are returned unchanged.

    Args:
        obj: The object to convert.

    Returns:
        A dict representation of *obj* if it is a dataclass, otherwise the
        original object (or a recursively converted container).
    """
    # Dataclass instance (but not the class itself)
    if is_dataclass(obj) and not isinstance(obj, type):
        result = {}
        for f in fields(obj):
            value = getattr(obj, f.name)
            result[f.name] = dataclass_to_dict(value)
        return result

    # Mapping types
    if isinstance(obj, dict):
        return {k: dataclass_to_dict(v) for k, v in obj.items()}

    # Iterable containers (list, tuple, set)
    if isinstance(obj, (list, tuple, set)):
        converted = [dataclass_to_dict(v) for v in obj]
        if isinstance(obj, list):
            return converted
        if isinstance(obj, tuple):
            return tuple(converted)
        return set(converted)

    # Fallback: return as‑is
    return obj
