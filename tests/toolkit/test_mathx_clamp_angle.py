import math

import pytest

from app.toolkit.mathx import clamp_angle


def test_clamp_angle_basic_cases() -> None:
    # Zero stays zero
    assert clamp_angle(0.0) == 0.0
    # Positive angle within range stays unchanged
    assert clamp_angle(0.5) == pytest.approx(0.5)
    # Negative angle within range stays unchanged
    assert clamp_angle(-0.75) == pytest.approx(-0.75)


def test_clamp_angle_edge_cases() -> None:
    # Exact pi maps to -pi (due to the chosen interval)
    assert clamp_angle(math.pi) == pytest.approx(-math.pi)
    # -pi stays -pi
    assert clamp_angle(-math.pi) == pytest.approx(-math.pi)
    # Multiples of 2π return the same angle (zero)
    assert clamp_angle(2 * math.pi) == pytest.approx(0.0)
    # 3π wraps to -π
    assert clamp_angle(3 * math.pi) == pytest.approx(-math.pi)
    # -3π also wraps to -π
    assert clamp_angle(-3 * math.pi) == pytest.approx(-math.pi)


def test_clamp_angle_range_enforcement() -> None:
    # Random large angle should be within the interval after clamping
    large_angle = 12345.678
    result = clamp_angle(large_angle)
    assert -math.pi <= result <= math.pi
