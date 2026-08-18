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
