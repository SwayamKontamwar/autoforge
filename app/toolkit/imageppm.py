"""Utility functions for handling simple PPM‑style image data.

The module currently provides helpers for creating and mutating a blank RGB
pixel grid and for serialising the grid to the ASCII PPM (P3) format.

Typical usage::

    >>> from app.toolkit.imageppm import ppm_new, ppm_set_pixel, ppm_to_p3
    >>> grid = ppm_new(2, 1)
    >>> ppm_set_pixel(grid, 0, 0, (255, 0, 128))
    >>> print(ppm_to_p3(grid))
    P3
    2 1
    255
    255 0 128 0 0 0

The functions validate their inputs and raise :class:`ValueError` for
negative dimensions or invalid colour values. Zero width or height yields an
empty list, matching the behaviour of other matrix‑creation helpers in the
toolkit.
"""

from __future__ import annotations

from typing import List, Tuple


def ppm_new(width: int, height: int) -> List[List[Tuple[int, int, int]]]:
    """Create a blank RGB pixel grid of the given *width* and *height*.

    Each pixel is represented as a ``(r, g, b)`` tuple with values in the range
    0‑255. The grid is initialised to black (0, 0, 0).

    Args:
        width: Number of columns (pixels per row).
        height: Number of rows.

    Returns:
        A list of *height* rows, each a list of *width* black pixel tuples.

    Raises:
        ValueError: If *width* or *height* is negative.
    """
    if width < 0 or height < 0:
        raise ValueError("width and height must be non‑negative")
    if width == 0 or height == 0:
        return []
    return [[(0, 0, 0) for _ in range(width)] for _ in range(height)]


def ppm_set_pixel(
    grid: List[List[Tuple[int, int, int]]],
    x: int,
    y: int,
    colour: Tuple[int, int, int],
) -> None:
    """Set the pixel at coordinates *(x, y)* to *colour*.

    The origin *(0, 0)* is the top‑left corner. ``x`` is the column index,
    ``y`` the row index.

    Args:
        grid: The pixel grid returned by :func:`ppm_new`.
        x: Column index.
        y: Row index.
        colour: A ``(r, g, b)`` tuple with each component in ``0‑255``.

    Raises:
        IndexError: If ``x`` or ``y`` is outside the bounds of *grid*.
        ValueError: If *colour* is not a three‑element tuple of ints in range.
    """
    if not (0 <= y < len(grid)) or not (0 <= x < len(grid[0])):
        raise IndexError("pixel coordinates out of bounds")
    if (
        not isinstance(colour, tuple)
        or len(colour) != 3
        or any(not isinstance(c, int) or c < 0 or c > 255 for c in colour)
    ):
        raise ValueError("colour must be a tuple of three ints in 0‑255")
    grid[y][x] = colour


def ppm_to_p3(grid: List[List[Tuple[int, int, int]]]) -> str:
    """Serialise *grid* to an ASCII PPM (P3) string.

    The returned string follows the PPM specification:

    * Header line ``P3``
    * Width and height line
    * Maximum colour value line (always ``255``)
    * Pixel data: each pixel's ``r g b`` values separated by spaces,
      rows written in order from top to bottom.

    An empty grid yields a header with width and height ``0 0`` and no
    pixel data.

    Args:
        grid: A pixel grid as produced by :func:`ppm_new`.

    Returns:
        A string containing the PPM representation.
    """
    # Determine dimensions
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    # Header
    lines = ["P3", f"{width} {height}", "255"]

    # Pixel data
    if width and height:
        pixel_parts: List[str] = []
        for row in grid:
            for r, g, b in row:
                pixel_parts.extend([str(r), str(g), str(b)])
        # Join all pixel components with spaces; a trailing newline is added later
        lines.append(" ".join(pixel_parts))

    # Ensure final newline
    return "\n".join(lines) + "\n"
