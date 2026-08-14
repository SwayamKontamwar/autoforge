"""Tests for the ``set_bit`` utility."""

from __future__ import annotations

import pytest

from app.toolkit import set_bit


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
