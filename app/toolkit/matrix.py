"""Matrix utilities for the toolkit.

Provides functions to create and manipulate simple 2‑dimensional matrices.
"""

from __future__ import annotations

from typing import List


def mat_zeros(rows: int, cols: int) -> List[List[int]]:
    """Return a matrix (list of lists) filled with zeros.

    Args:
        rows: Number of rows in the matrix. Must be non‑negative.
        cols: Number of columns in each row. Must be non‑negative.

    Returns:
        A list containing ``rows`` sub‑lists, each of length ``cols``,
        populated with ``0``. If either dimension is zero, an empty list is
        returned.

    Raises:
        ValueError: If ``rows`` or ``cols`` is negative.
    """
    if rows < 0 or cols < 0:
        raise ValueError("rows and cols must be non‑negative integers")
    if rows == 0 or cols == 0:
        return []
    return [[0 for _ in range(cols)] for _ in range(rows)]
