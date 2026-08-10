"""Randomness utilities."""

from __future__ import annotations

import secrets
import string


def random_string(length: int) -> str:
    """Return a random alphanumeric string of *length* characters.

    The string consists of ASCII letters (both cases) and digits.
    If *length* is non‑positive, an empty string is returned.
    """
    if length <= 0:
        return ""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
