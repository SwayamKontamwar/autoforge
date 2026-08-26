"""Tests for the ``set_bit`` and ``clear_bit`` utilities."""

from __future__ import annotations

import pytest

from app.toolkit import clear_bit, set_bit


def test_set_bit_basic():
    """Setting bits on a clean value."""
    assert set_bit(0, 0) == 1
    # 0b101 (5) with bit 1 set becomes 0b111 (7)
    assert set_bit(5, 1) == 7


def test_set_bit_already_set():
    """Setting a bit that is already 1 leaves the value unchanged."""
    assert set_bit(8, 3) == 8  # 0b1000 already has bit 3 set


def test_set_bit_negative_position():
    """Negative positions are rejected."""
    with pytest.raises(ValueError):
        set_bit(1, -1)


def test_clear_bit_basic():
    """Clearing bits on a value where the bit is set."""
    # 0b111 (7) clearing bit 1 yields 0b101 (5)
    assert clear_bit(7, 1) == 5
    # 0b1000 (8) clearing bit 3 yields 0b0000 (0)
    assert clear_bit(8, 3) == 0


def test_clear_bit_already_cleared():
    """Clearing a bit that is already 0 leaves the value unchanged."""
    # 0b1010 (10) clearing bit 0 (already 0) stays 10
    assert clear_bit(10, 0) == 10
    # clearing a high position beyond current bits does nothing
    assert clear_bit(2, 5) == 2


def test_clear_bit_negative_position():
    """Negative positions are rejected for clear_bit as well."""
    with pytest.raises(ValueError):
        clear_bit(1, -2)
