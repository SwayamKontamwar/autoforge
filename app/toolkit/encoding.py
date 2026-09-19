"""Base‑62 encoding utilities for the autoforge toolkit.

Provides a function to encode a non‑negative integer into a base‑62 string using
the characters 0‑9, a‑z, and A‑Z.
"""

from __future__ import annotations

from typing import Final

_ALPHABET: Final = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_BASE: Final = 62

# Bitcoin‑style Base58 alphabet (no 0, O, I, l)
_ALPHABET_BASE58: Final = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BASE58: Final = 58

__all__: list[str] = [
    "base62_encode",
    "base62_decode",
    "base58_encode",
    "base58_decode",
]


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


def base62_decode(value: str) -> int:
    """Decode a base‑62 string back to an integer.

    Args:
        value: A non‑empty string consisting only of base‑62 characters.

    Returns:
        The integer represented by ``value``.

    Raises:
        TypeError: If ``value`` is not a ``str``.
        ValueError: If ``value`` is empty or contains invalid characters.
    """
    if not isinstance(value, str):
        raise TypeError("value must be a str")
    if not value:
        raise ValueError("value must be non‑empty")
    num = 0
    for char in value:
        try:
            idx = _ALPHABET.index(char)
        except ValueError as exc:
            raise ValueError(f"invalid character {char!r}") from exc
        num = num * _BASE + idx
    return num


def base58_encode(value: int) -> str:
    """Encode a non‑negative integer to a Bitcoin‑style base‑58 string.

    Args:
        value: An integer greater than or equal to ``0``.

    Returns:
        The base‑58 representation of ``value`` without leading zeros.

    Raises:
        TypeError: If ``value`` is not an ``int``.
        ValueError: If ``value`` is negative.
    """
    if not isinstance(value, int):
        raise TypeError("value must be an int")
    if value < 0:
        raise ValueError("value must be non‑negative")
    if value == 0:
        return _ALPHABET_BASE58[0]

    digits: list[str] = []
    while value:
        value, rem = divmod(value, _BASE58)
        digits.append(_ALPHABET_BASE58[rem])
    return "".join(reversed(digits))


def base58_decode(value: str) -> int:
    """Decode a Bitcoin‑style base‑58 string back to an integer.

    Args:
        value: A non‑empty string consisting only of base‑58 characters.

    Returns:
        The integer represented by ``value``.

    Raises:
        TypeError: If ``value`` is not a ``str``.
        ValueError: If ``value`` is empty or contains invalid characters.
    """
    if not isinstance(value, str):
        raise TypeError("value must be a str")
    if not value:
        raise ValueError("value must be non‑empty")
    num = 0
    for char in value:
        try:
            idx = _ALPHABET_BASE58.index(char)
        except ValueError as exc:
            raise ValueError(f"invalid character {char!r}") from exc
        num = num * _BASE58 + idx
    return num
