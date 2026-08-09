"""Validation utilities for the toolkit.

Provides pragmatic checks for common data formats without pulling in heavy
dependencies. Functions return ``True`` when the input satisfies the check,
``False`` otherwise.
"""

from __future__ import annotations

import re

# Simple but practical email regex:
# - local part: alphanumerics and allowed special characters
# - domain part: labels separated by dots, each label starts and ends with alphanum,
#   may contain hyphens inside.
_EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$"
)


def is_email(value: str) -> bool:
    """Return ``True`` if *value* looks like a valid email address.

    The check is deliberately pragmatic: it validates the general structure
    ``local@domain`` using a regular expression that covers the vast majority
    of real‑world addresses while remaining readable and fast.

    Args:
        value: The string to validate.

    Returns:
        ``True`` if *value* matches the email pattern, ``False`` otherwise.
    """
    if not isinstance(value, str):
        return False
    return bool(_EMAIL_REGEX.fullmatch(value))
