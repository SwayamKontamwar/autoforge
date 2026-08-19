import pytest

from app.toolkit.numbers import clamp, lerp


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


def test_lerp_typical() -> None:
    # Midpoint interpolation
    assert lerp(0, 10, 0.5) == 5
    # Start and end boundaries
    assert lerp(5, 15, 0.0) == 5
    assert lerp(5, 15, 1.0) == 15


def test_lerp_edge_cases() -> None:
    # Extrapolation before start
    assert lerp(10, 20, -0.5) == 5
    # Extrapolation beyond end
    assert lerp(10, 20, 1.5) == 25
