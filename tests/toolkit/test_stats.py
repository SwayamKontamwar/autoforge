import pytest

from app.toolkit.stats import geometric_mean, harmonic_mean, weighted_mean


def test_geometric_mean_basic() -> None:
    # The geometric mean of 1, 3, 9 is 3.
    assert geometric_mean([1, 3, 9]) == pytest.approx(3.0)


def test_geometric_mean_edge_cases() -> None:
    # Empty iterable should raise ValueError.
    with pytest.raises(ValueError):
        geometric_mean([])

    # Non‑positive values should raise ValueError.
    with pytest.raises(ValueError):
        geometric_mean([2, 0, 5])


def test_harmonic_mean_basic() -> None:
    # Harmonic mean of 1, 2, 4 is 3 / (1 + 0.5 + 0.25) = 1.714285...
    assert harmonic_mean([1, 2, 4]) == pytest.approx(1.7142857142857142)


def test_harmonic_mean_edge_cases() -> None:
    # Empty iterable should raise ValueError.
    with pytest.raises(ValueError):
        harmonic_mean([])

    # Non‑positive values should raise ValueError.
    with pytest.raises(ValueError):
        harmonic_mean([2, 0, 5])


def test_weighted_mean_basic() -> None:
    # Weighted mean with weights summing to 1.
    assert weighted_mean([1, 2, 3], [0.2, 0.3, 0.5]) == pytest.approx(2.3)


def test_weighted_mean_edge_cases() -> None:
    # Empty inputs raise ValueError.
    with pytest.raises(ValueError):
        weighted_mean([], [])

    # Mismatched lengths raise ValueError.
    with pytest.raises(ValueError):
        weighted_mean([1, 2], [0.5])

    # Zero total weight raises ValueError.
    with pytest.raises(ValueError):
        weighted_mean([1, 2], [0, 0])
