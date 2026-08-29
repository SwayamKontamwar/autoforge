"""Utility functions for handling simple PPM‑style image data.

The module currently provides a single helper, :func:`ppm_new`, which creates a
blank RGB pixel grid (a list of rows, each row a list of ``(r, g, b)`` tuples)
filled with black pixels (0, 0, 0).

Typical usage::

    >>> from app.toolkit.imageppm import ppm_new
    >>> ppm_new(2, 1)
    [[(0, 0, 0), (0, 0, 0)]]

The function validates its inputs and raises :class:`ValueError` for negative
dimensions. Zero width or height yields an empty list, matching the behaviour
of other matrix‑creation helpers in the toolkit.
"""

from __future__ import annotations

from typing import List, Tuple


def ppm_new(width: int, height: int) -> List[List[Tuple[int, int, int]]]:
    """Create a blank RGB pixel grid of the given *width* and *height*.

    Each pixel is represented as a ``(r, g, b)`` tuple with values in the range
    0‑255. The grid is initialised to black (0, 0, 0).

    Args:
        width: Number of columns (pixels per row). Must be non‑negative.
        height: Number of rows. Must be non‑negative.

    Returns:
        A list of *height* rows, each containing *width* ``(0, 0, 0)`` tuples.
        If either dimension is zero, an empty list is returned.

    Raises:
        ValueError: If *width* or *height* is negative.
    """
    if width < 0 or height < 0:
        raise ValueError("width and height must be non‑negative integers")
    if width == 0 or height == 0:
        return []
    # Create a single row of black pixels and replicate it for each row.
    row: List[Tuple[int, int, int]] = [(0, 0, 0) for _ in range(width)]
    return [list(row) for _ in range(height)]


def ppm_set_pixel(
    grid: List[List[Tuple[int, int, int]]],
    x: int,
    y: int,
    colour: Tuple[int, int, int],
) -> None:
    """Set the pixel at coordinates *(x, y)* to *colour*.

    The grid is a list of rows (height) where each row is a list of pixel
    tuples (width). ``x`` is the column index and ``y`` is the row index,
    both zero‑based.

    Args:
        grid: The pixel grid returned by :func:`ppm_new`.
        x: Column index (0 ≤ x < width).
        y: Row index (0 ≤ y < height).
        colour: A ``(r, g, b)`` tuple with each component in the range 0‑255.

    Raises:
        IndexError: If ``x`` or ``y`` is outside the bounds of the grid.
        ValueError: If ``colour`` is not a three‑element tuple of ints in 0‑255.
    """
    # Validate coordinates.
    if y < 0 or y >= len(grid):
        raise IndexError("y coordinate out of bounds")
    if len(grid) == 0:
        raise IndexError("grid is empty")
    if x < 0 or x >= len(grid[0]):
        raise IndexError("x coordinate out of bounds")

    # Validate colour.
    if (
        not isinstance(colour, tuple)
        or len(colour) != 3
        or any(not isinstance(c, int) or c < 0 or c > 255 for c in colour)
    ):
        raise ValueError("colour must be a tuple of three ints in 0‑255")

    grid[y][x] = colour
