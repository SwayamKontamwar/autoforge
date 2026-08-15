import pytest

from app.toolkit.stats import geometric_mean


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
