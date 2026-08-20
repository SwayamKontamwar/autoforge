"""Base‑62 encoding utilities for the autoforge toolkit.

Provides a function to encode a non‑negative integer into a base‑62 string using
the characters 0‑9, a‑z, and A‑Z.
"""

from __future__ import annotations

from typing import Final

_ALPHABET: Final = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_BASE: Final = 62

__all__: list[str] = ["base62_encode", "base62_decode"]


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


def base62_decode(text: str) -> int:
    """Decode a base‑62 string back to an integer.

    The decoding expects characters from the same alphabet used by
    :func:`base62_encode`. Leading zeros are allowed and are ignored in the
    numeric value.

    Args:
        text: A string consisting only of characters ``0‑9``, ``a‑z``, ``A‑Z``.

    Returns:
        The integer represented by ``text``.

    Raises:
        TypeError: If ``text`` is not a ``str``.
        ValueError: If ``text`` is empty or contains characters outside the
            base‑62 alphabet.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    if not text:
        raise ValueError("text must be non‑empty")
    value = 0
    for char in text:
        try:
            digit = _ALPHABET.index(char)
        except ValueError as exc:
            raise ValueError(f"invalid character '{char}' for base‑62") from exc
        value = value * _BASE + digit
    return value
