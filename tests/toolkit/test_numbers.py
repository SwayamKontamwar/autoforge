import pytest

from app.toolkit.numbers import clamp


def test_clamp_basic() -> None:
    assert clamp(5, 1, 10) == 5
    assert clamp(-1, 0, 5) == 0
    assert clamp(100, 0, 50) == 50


def test_clamp_edge_cases() -> None:
    assert clamp(0, 0, 10) == 0
    assert clamp(10, 0, 10) == 10


def test_clamp_invalid_range() -> None:
    with pytest.raises(ValueError):
        clamp(5, 10, 0)
