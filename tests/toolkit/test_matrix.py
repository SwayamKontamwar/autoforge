import pytest

from app.toolkit.matrix import mat_add, mat_identity, mat_zeros


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


def test_mat_identity_typical() -> None:
    """Typical usage: 3 × 3 identity matrix."""
    expected = [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ]
    assert mat_identity(3) == expected


def test_mat_identity_edge_cases() -> None:
    """Edge cases: zero size and negative input."""
    # Zero size yields empty list
    assert mat_identity(0) == []
    # Negative size raises ValueError
    with pytest.raises(ValueError):
        mat_identity(-5)


def test_mat_add_typical() -> None:
    """Typical element‑wise addition of two matrices."""
    a = [[1, 2, 3], [4, 5, 6]]
    b = [[6, 5, 4], [3, 2, 1]]
    expected = [[7, 7, 7], [7, 7, 7]]
    assert mat_add(a, b) == expected


def test_mat_add_edge_cases() -> None:
    """Edge cases: empty matrices and mismatched dimensions."""
    # Adding two empty matrices yields an empty matrix
    assert mat_add([], []) == []
    # Mismatched row count raises ValueError
    with pytest.raises(ValueError):
        mat_add([[1]], [])
    # Mismatched column count raises ValueError
    with pytest.raises(ValueError):
        mat_add([[1, 2]], [[3]])
