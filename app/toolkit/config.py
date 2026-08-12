"""Configuration helpers for environment variables.

Provides utilities to read typed values from the process environment with
reasonable defaults and validation. Currently includes a boolean reader
``get_env_bool`` which interprets common truthy/falsy strings.
"""

from __future__ import annotations

import os
from typing import Final

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
