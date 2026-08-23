"""Geometry utilities.

Provides basic geometric calculations for 2‑D points.
"""

from __future__ import annotations

import math
from typing import Tuple, Union

Number = Union[int, float]
Point2D = Tuple[Number, Number]


def distance_2d(p1: Point2D, p2: Point2D) -> float:
    """Return Euclidean distance between two 2‑D points.

    Args:
        p1: (x, y) coordinates of the first point.
        p2: (x, y) coordinates of the second point.

    Returns:
        The Euclidean distance as a float.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.hypot(dx, dy)


def manhattan_distance(p1: Point2D, p2: Point2D) -> float:
    """Return Manhattan (L1) distance between two 2‑D points.

    The Manhattan distance is the sum of the absolute differences of the
    Cartesian coordinates.

    Args:
        p1: (x, y) coordinates of the first point.
        p2: (x, y) coordinates of the second point.

    Returns:
        The Manhattan distance as a float.
    """
    dx = abs(p2[0] - p1[0])
    dy = abs(p2[1] - p1[1])
    return float(dx + dy)
