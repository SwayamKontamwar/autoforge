"""Bit manipulation utilities.

This module provides small helpers for working with integer bit patterns.
"""

from __future__ import annotations


def set_bit(value: int, position: int) -> int:
    """Return *value* with the bit at *position* set to ``1``.

    Args:
        value: Integer whose bits are to be modified.
        position: Zero‑based index of the bit to set. Must be non‑negative.

    Returns:
        New integer with the specified bit set.

    Raises:
        ValueError: If *position* is negative.
    """
    if position < 0:
        raise ValueError("position must be non‑negative")
    return value | (1 << position)


def clear_bit(value: int, position: int) -> int:
    """Return *value* with the bit at *position* cleared to ``0``.

    Args:
        value: Integer whose bits are to be modified.
        position: Zero‑based index of the bit to clear. Must be non‑negative.

    Returns:
        New integer with the specified bit cleared.

    Raises:
        ValueError: If *position* is negative.
    """
    if position < 0:
        raise ValueError("position must be non‑negative")
    return value & ~(1 << position)
