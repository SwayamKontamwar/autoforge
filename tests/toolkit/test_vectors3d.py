import pytest

from app.toolkit.vectors3d import v3_add


def test_v3_add_typical() -> None:
    """Typical component‑wise addition of two 3‑vectors."""
    v1 = (1.0, 0.5, 0.0)
    v2 = (1.0, 0.5, 0.0)
    assert v3_add(v1, v2) == (2.0, 1.0, 0.0)


def test_v3_add_edge_cases() -> None:
    """Edge cases: zero vector and validation of length."""
    # Adding a zero vector returns the original vector (rounded)
    zero = (0, 0, 0)
    v = (3, -4, 5)
    assert v3_add(v, zero) == (3, -4, 5)

    # Vectors with incorrect length raise ValueError
    with pytest.raises(ValueError):
        v3_add((1, 2), (3, 4, 5))

    with pytest.raises(ValueError):
        v3_add((1, 2, 3, 4), (0, 0, 0))
