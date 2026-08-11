import pytest

from app.toolkit.geometry import distance_2d


def test_distance_2d_typical() -> None:
    assert distance_2d((0, 0), (3, 4)) == 5.0


def test_distance_2d_edge_cases() -> None:
    # Same point yields zero distance
    assert distance_2d((1.5, -2.5), (1.5, -2.5)) == 0.0
    # Negative coordinates
    assert distance_2d((-1, -1), (2, 3)) == pytest.approx(5.0)
