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


def mat_identity(size: int) -> List[List[int]]:
    """Return an identity matrix of the given size.

    An identity matrix is a square matrix with ``1`` on the main diagonal
    and ``0`` elsewhere.

    Args:
        size: The number of rows and columns. Must be non‑negative.

    Returns:
        A ``size`` × ``size`` matrix where ``matrix[i][j]`` is ``1`` if
        ``i == j`` and ``0`` otherwise. If ``size`` is ``0`` an empty list
        is returned.

    Raises:
        ValueError: If ``size`` is negative.
    """
    if size < 0:
        raise ValueError("size must be a non‑negative integer")
    if size == 0:
        return []
    return [[1 if i == j else 0 for j in range(size)] for i in range(size)]


def mat_add(a: List[List[int]], b: List[List[int]]) -> List[List[int]]:
    """Return the element‑wise sum of two matrices.

    Both matrices must have the same dimensions (identical number of rows
    and identical number of columns in each corresponding row).  If the
    dimensions differ a :class:`ValueError` is raised.

    Args:
        a: First matrix.
        b: Second matrix.

    Returns:
        A new matrix where each element is ``a[i][j] + b[i][j]``.

    Raises:
        ValueError: If the matrices have mismatched dimensions.
    """
    if len(a) != len(b):
        raise ValueError("matrices must have the same number of rows")
    if not a:  # both are empty
        return []
    result: List[List[int]] = []
    for row_a, row_b in zip(a, b):
        if len(row_a) != len(row_b):
            raise ValueError("matrices must have the same number of columns")
        result.append([x + y for x, y in zip(row_a, row_b)])
    return result
