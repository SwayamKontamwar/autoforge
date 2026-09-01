import pytest

from app.toolkit.numbers import clamp, inverse_lerp, lerp


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


def test_inverse_lerp_typical() -> None:
    # Value exactly in the middle
    assert inverse_lerp(0, 10, 5) == 0.5
    # Value at start
    assert inverse_lerp(10, 20, 10) == 0.0
    # Value at end
    assert inverse_lerp(10, 20, 20) == 1.0


def test_inverse_lerp_extrapolation() -> None:
    # Value before start yields negative fraction
    assert inverse_lerp(10, 20, 5) == -0.5
    # Value after end yields fraction > 1
    assert inverse_lerp(10, 20, 25) == 1.5


def test_inverse_lerp_invalid_range() -> None:
    # start == end should raise ValueError
    with pytest.raises(ValueError):
        inverse_lerp(5, 5, 5)
