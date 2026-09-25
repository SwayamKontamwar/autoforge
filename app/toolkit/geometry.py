"""Geometry utilities.

Provides basic geometric calculations for 2‑D points.
"""

from __future__ import annotations

import math
from typing import Tuple, Union

Number = Union[int, float]
Point2D = Tuple[Number, Number]
Rect = Tuple[Number, Number, Number, Number]  # (x1, y1, x2, y2)


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


def haversine(
    p1: Tuple[Number, Number],
    p2: Tuple[Number, Number],
    radius: float = 6371.0,
) -> float:
    """Return the great‑circle distance between two latitude/longitude points.

    The points are given as (latitude, longitude) pairs in decimal degrees.
    The default radius corresponds to the mean Earth radius in kilometres.

    Args:
        p1: (lat, lon) of the first point in degrees.
        p2: (lat, lon) of the second point in degrees.
        radius: Radius of the sphere (default 6371.0 km).

    Returns:
        Distance between the two points along the surface of the sphere.
    """
    lat1, lon1 = map(math.radians, p1)
    lat2, lon2 = map(math.radians, p2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    sin_dlat = math.sin(dlat / 2.0)
    sin_dlon = math.sin(dlon / 2.0)

    a = sin_dlat**2 + math.cos(lat1) * math.cos(lat2) * sin_dlon**2
    c = 2.0 * math.asin(math.sqrt(a))

    return radius * c


def point_in_rect(point: Point2D, rect: Rect) -> bool:
    """Return whether a point lies inside a rectangle (inclusive of edges).

    The rectangle is defined by two opposite corners ``(x1, y1)`` and
    ``(x2, y2)``.  The order of the corners does not matter; the function
    normalises them to the minimum and maximum extents.

    Args:
        point: ``(x, y)`` coordinates of the point to test.
        rect: ``(x1, y1, x2, y2)`` defining the rectangle.

    Returns:
        ``True`` if the point is inside the rectangle or on its border,
        ``False`` otherwise.
    """
    x, y = point
    x1, y1, x2, y2 = rect
    min_x, max_x = (x1, x2) if x1 <= x2 else (x2, x1)
    min_y, max_y = (y1, y2) if y1 <= y2 else (y2, y1)
    return min_x <= x <= max_x and min_y <= y <= max_y
