"""Configuration helpers for environment variables.

Provides utilities to read typed values from the process environment with
reasonable defaults and validation. Currently includes a boolean reader
``get_env_bool`` which interprets common truthy/falsy strings.
"""

from __future__ import annotations

import os
from typing import Any, Final

# Accepted true/false strings (case‑insensitive)
_TRUE_VALUES: Final[set[str]] = {"true", "1", "yes", "y", "on"}
_FALSE_VALUES: Final[set[str]] = {"false", "0", "no", "n", "off"}


def get_env_bool(name: str, default: bool = False) -> bool:
    """Return a boolean environment variable.

    The function reads ``name`` from ``os.getenv``. If the variable is not set,
    ``default`` is returned. Otherwise the value is stripped and compared
    case‑insensitively against known true/false literals.

    Accepted true values: ``"true", "1", "yes", "y", "on"``.
    Accepted false values: ``"false", "0", "no", "n", "off"``.

    Args:
        name: Environment variable name.
        default: Value to return when the variable is missing.

    Returns:
        ``True`` or ``False`` according to the variable's content.

    Raises:
        ValueError: If the variable is set to a value that is not recognised as
            true or false.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in _TRUE_VALUES:
        return True
    if value in _FALSE_VALUES:
        return False
    raise ValueError(f"Environment variable {name!r} has unrecognised boolean value: {raw!r}")


def get_env_int(name: str, default: int = 0) -> int:
    """Return an integer environment variable.

    The function reads ``name`` from ``os.getenv``. If the variable is not set,
    ``default`` is returned. Otherwise the value is stripped and converted to
    ``int``. Whitespace around the value is ignored.

    Args:
        name: Environment variable name.
        default: Value to return when the variable is missing.

    Returns:
        The integer value of the environment variable.

    Raises:
        ValueError: If the variable is set but cannot be parsed as an integer.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except Exception as exc:
        raise ValueError(f"Environment variable {name!r} has non‑integer value: {raw!r}") from exc


def get_env_list(name: str, default: list[str] | None = None) -> list[str]:
    """Return a list environment variable.

    The function reads ``name`` from ``os.getenv``. If the variable is not set,
    ``default`` (or an empty list if ``default`` is ``None``) is returned.
    The variable's value is split on commas, each element is stripped of
    surrounding whitespace, and empty strings are discarded.
    """
    raw = os.getenv(name)
    if raw is None:
        return [] if default is None else default
    # Split on commas and strip whitespace
    parts = [part.strip() for part in raw.split(",")]
    # Filter out empty strings
    return [part for part in parts if part]


def deep_get(data: dict[str, Any], path: str, default: Any = None) -> Any:
    """Retrieve a nested value from ``data`` using a dotted ``path``.

    Args:
        data: The dictionary to search.
        path: Dotted path string, e.g. ``"a.b.c"``.
        default: Value to return if any part of the path is missing.

    Returns:
        The value found at the path, or ``default`` if the path cannot be fully
        resolved.
    """
    if not path:
        return default
    current: Any = data
    for key in path.split("."):
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current
