import pytest

from app.toolkit.matrix import mat_zeros


def test_mat_zeros_typical() -> None:
    """Typical usage: a 2 × 3 matrix of zeros."""
    expected = [[0, 0, 0], [0, 0, 0]]
    assert mat_zeros(2, 3) == expected


def test_mat_zeros_edge_cases() -> None:
    """Edge cases: zero dimensions and negative inputs."""
    # Zero rows yields an empty list
    assert mat_zeros(0, 5) == []
    # Zero columns yields an empty list as well
    assert mat_zeros(3, 0) == []
    # Negative dimensions raise ValueError
    with pytest.raises(ValueError):
        mat_zeros(-1, 4)
    with pytest.raises(ValueError):
        mat_zeros(4, -2)
