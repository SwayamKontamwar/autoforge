"""Base‑62 encoding utilities for the autoforge toolkit.

Provides a function to encode a non‑negative integer into a base‑62 string using
the characters 0‑9, a‑z, and A‑Z.
"""

from __future__ import annotations

from typing import Final

_ALPHABET: Final = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_BASE: Final = 62

__all__: list[str] = ["base62_encode"]


def base62_encode(value: int) -> str:
    """Encode a non‑negative integer to a base‑62 string.

    The encoding uses the characters ``0‑9``, ``a‑z``, and ``A‑Z`` as digits,
    where ``0`` represents zero and ``Z`` represents sixty‑one.

    Args:
        value: An integer greater than or equal to ``0``.

    Returns:
        The base‑62 representation of ``value`` without leading zeros.

    Raises:
        TypeError: If ``value`` is not an ``int``.
        ValueError: If ``value`` is negative.
    """
    if not isinstance(value, int):
        raise TypeError("value must be an int")
    if value < 0:
        raise ValueError("value must be non‑negative")
    if value == 0:
        return _ALPHABET[0]

    digits: list[str] = []
    while value:
        value, rem = divmod(value, _BASE)
        digits.append(_ALPHABET[rem])
    return "".join(reversed(digits))
