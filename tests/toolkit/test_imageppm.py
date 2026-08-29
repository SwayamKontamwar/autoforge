import pytest

from app.toolkit.imageppm import ppm_new, ppm_set_pixel


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


def test_ppm_set_pixel_typical_and_edge_cases() -> None:
    grid = ppm_new(2, 2)
    # Set a pixel inside the grid
    ppm_set_pixel(grid, 1, 0, (10, 20, 30))
    assert grid[0][1] == (10, 20, 30)

    # Out‑of‑bounds coordinates raise IndexError
    with pytest.raises(IndexError):
        ppm_set_pixel(grid, 2, 0, (0, 0, 0))
    with pytest.raises(IndexError):
        ppm_set_pixel(grid, -1, 0, (0, 0, 0))

    # Invalid colour raises ValueError
    with pytest.raises(ValueError):
        ppm_set_pixel(grid, 0, 0, (256, 0, 0))
    with pytest.raises(ValueError):
        ppm_set_pixel(grid, 0, 0, (0, -1, 0))
    with pytest.raises(ValueError):
        ppm_set_pixel(grid, 0, 0, (0, 0))  # wrong length
