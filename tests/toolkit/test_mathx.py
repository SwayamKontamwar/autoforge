import pytest

from app.toolkit.mathx import hypot


def test_hypot_typical_cases() -> None:
    # Classic 3‑4‑5 triangle
    assert hypot(3, 4) == pytest.approx(5.0)
    # Multiple components
    assert hypot(1, 2, 2) == pytest.approx(3.0)
    # Negative components should be treated as their absolute values
    assert hypot(-3, -4) == pytest.approx(5.0)


def test_hypot_edge_cases() -> None:
    # No components yields zero
    assert hypot() == 0.0
    # Single component returns its absolute value
    assert hypot(-7) == pytest.approx(7.0)
