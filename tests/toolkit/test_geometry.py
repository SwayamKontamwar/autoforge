import pytest

from app.toolkit.geometry import distance_2d, point_in_rect


def test_distance_2d_typical() -> None:
    assert distance_2d((0, 0), (3, 4)) == 5.0


def test_distance_2d_edge_cases() -> None:
    # Same point yields zero distance
    assert distance_2d((1.5, -2.5), (1.5, -2.5)) == 0.0
    # Negative coordinates
    assert distance_2d((-1, -1), (2, 3)) == pytest.approx(5.0)


def test_point_in_rect_basic() -> None:
    # Inside rectangle
    assert point_in_rect((0.5, 0.5), (0, 0, 1, 1)) is True
    # On edge should be considered inside
    assert point_in_rect((0, 0), (0, 0, 1, 1)) is True
    # Outside rectangle
    assert point_in_rect((2, 2), (0, 0, 1, 1)) is False
