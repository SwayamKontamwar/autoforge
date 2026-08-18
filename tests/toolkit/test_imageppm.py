import pytest

from app.toolkit.imageppm import ppm_new


def test_ppm_new_typical() -> None:
    """A 2 × 3 grid should contain six black pixels."""
    result = ppm_new(3, 2)
    expected = [
        [(0, 0, 0), (0, 0, 0), (0, 0, 0)],
        [(0, 0, 0), (0, 0, 0), (0, 0, 0)],
    ]
    assert result == expected


def test_ppm_new_edge_cases() -> None:
    # Zero dimensions yield an empty list
    assert ppm_new(0, 5) == []
    assert ppm_new(4, 0) == []

    # Negative dimensions raise ValueError
    with pytest.raises(ValueError):
        ppm_new(-1, 3)
    with pytest.raises(ValueError):
        ppm_new(3, -2)
