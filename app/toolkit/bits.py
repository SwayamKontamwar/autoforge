"""Bit manipulation utilities.

This module provides small helpers for working with integer bit patterns.
"""

from __future__ import annotations


def set_bit(value: int, position: int) -> int:
    """Return ``value`` with the bit at ``position`` set to 1.

    Raises:
        ValueError: If ``position`` is negative.
    """
    if position < 0:
        raise ValueError("bit position must be non‑negative")
    return value | (1 << position)


def clear_bit(value: int, position: int) -> int:
    """Return ``value`` with the bit at ``position`` cleared to 0.

    Raises:
        ValueError: If ``position`` is negative.
    """
    if position < 0:
        raise ValueError("bit position must be non‑negative")
    return value & ~(1 << position)


def toggle_bit(value: int, position: int) -> int:
    """Return ``value`` with the bit at ``position`` flipped.

    Raises:
        ValueError: If ``position`` is negative.
    """
    if position < 0:
        raise ValueError("bit position must be non‑negative")
    return value ^ (1 << position)


def highest_set_bit(value: int) -> int:
    """Return the index (0‑based) of the highest set bit in ``value``.

    If ``value`` is zero, ``-1`` is returned. ``value`` must be a
    non‑negative integer; a negative ``value`` raises ``ValueError``.
    """
    if value < 0:
        raise ValueError("value must be non‑negative")
    if value == 0:
        return -1
    # ``int.bit_length()`` returns the number of bits necessary to represent
    # the integer in binary, excluding the sign and leading zeros.
    return value.bit_length() - 1
