import pytest

from app.toolkit.mathx import factorial_iter, hypot


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


def test_factorial_iter_typical_and_edge_cases() -> None:
    # Typical values
    assert factorial_iter(0) == 1
    assert factorial_iter(5) == 120
    assert factorial_iter(10) == 3628800
    # Large value (20!)
    assert factorial_iter(20) == 2432902008176640000
    # Negative input raises ValueError
    with pytest.raises(ValueError):
        factorial_iter(-1)
    # Non‑integer input raises TypeError
    with pytest.raises(TypeError):
        factorial_iter(3.5)
