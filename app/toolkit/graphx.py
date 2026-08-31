"""Graph algorithms utilities.

Provides an implementation of the Floyd‑Warshall algorithm for computing the
all‑pairs shortest‑path distances of a weighted directed graph represented as a
matrix.

The matrix uses ``float('inf')`` (or ``None``) to denote the absence of an edge.
The function returns a new matrix with the shortest distances; the original
matrix is not mutated.
"""

from __future__ import annotations

from typing import List


def _normalize(matrix: List[List[float]]) -> List[List[float]]:
    """Return a copy of *matrix* where ``None`` entries are replaced with ``inf``."""
    n = len(matrix)
    result: List[List[float]] = [[float("inf")] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            val = matrix[i][j]
            if i == j:
                result[i][j] = 0.0
            elif val is None:
                result[i][j] = float("inf")
            else:
                result[i][j] = float(val)
    return result


def floyd_warshall(matrix: List[List[float]]) -> List[List[float]]:
    """Compute the all‑pairs shortest‑path distances using Floyd‑Warshall.

    Parameters
    ----------
    matrix:
        A square adjacency matrix where ``matrix[i][j]`` is the weight of the edge
        from *i* to *j*. ``float('inf')`` or ``None`` indicates no direct edge.

    Returns
    -------
    List[List[float]]
        A new matrix ``dist`` where ``dist[i][j]`` is the length of the shortest
        path from *i* to *j*. ``float('inf')`` is used when no path exists.
    """
    if not matrix:
        return []

    # Ensure we work on a clean copy with proper ``inf`` handling.
    dist = _normalize(matrix)

    n = len(dist)
    for k in range(n):
        dk = dist[k]
        for i in range(n):
            dik = dist[i][k]
            if dik == float("inf"):
                continue
            di = dist[i]
            for j in range(n):
                dkj = dk[j]
                if dkj == float("inf"):
                    continue
                new_dist = dik + dkj
                if new_dist < di[j]:
                    di[j] = new_dist
    return dist
