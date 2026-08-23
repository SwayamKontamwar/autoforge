from app.toolkit.geometry import manhattan_distance


def test_manhattan_distance_typical() -> None:
    """Typical Manhattan distance between (0,0) and (3,4) should be 7."""
    assert manhattan_distance((0, 0), (3, 4)) == 7.0


def test_manhattan_distance_edge_cases() -> None:
    # Same point yields zero distance
    assert manhattan_distance((1.5, -2.5), (1.5, -2.5)) == 0.0
    # Negative coordinates
    assert manhattan_distance((-1, -1), (2, 3)) == 7.0
