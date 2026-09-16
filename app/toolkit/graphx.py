"""Graph algorithms utilities.

Provides an implementation of the Floyd‑Warshall algorithm for computing the
all‑pairs shortest‑path distances of a weighted directed graph represented as a
matrix.

The matrix uses ``float('inf')`` (or ``None``) to denote the absence of an edge.
The function returns a new matrix with the shortest distances; the original
matrix is not mutated.
"""

from __future__ import annotations

import heapq
from typing import Callable, List, Optional


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


def astar(
    matrix: List[List[float]],
    start: int,
    goal: int,
    heuristic: Optional[Callable[[int, int], float]] = None,
) -> List[int]:
    """Return the shortest path from *start* to *goal* using the A* algorithm.

    The graph is given as an adjacency matrix where ``matrix[i][j]`` is the
    weight of the edge from *i* to *j*. ``float('inf')`` or ``None`` denotes the
    absence of a direct edge.

    Parameters
    ----------
    matrix:
        Square adjacency matrix representing the directed weighted graph.
    start:
        Index of the start node.
    goal:
        Index of the goal node.
    heuristic:
        Optional function ``h(node, goal)`` returning an estimated cost from
        *node* to *goal*. If omitted, a zero heuristic is used (equivalent to
        Dijkstra's algorithm).

    Returns
    -------
    List[int]
        List of node indices forming the shortest path, inclusive of *start*
        and *goal*. Returns an empty list if no path exists or if the graph is
        empty. If *start* equals *goal*, returns ``[start]``.
    """
    if not matrix:
        return []
    n = len(matrix)
    if not (0 <= start < n and 0 <= goal < n):
        return []
    if start == goal:
        return [start]

    # Normalise the matrix to have ``float('inf')`` for missing edges.
    adj = _normalize(matrix)

    # Default heuristic is zero.
    if heuristic is None:

        def heuristic(_node: int, _goal: int) -> float:  # type: ignore
            return 0.0

    # The open set holds tuples (f_score, g_score, node).
    open_heap: List[tuple[float, float, int]] = []
    heapq.heappush(open_heap, (heuristic(start, goal), 0.0, start))

    came_from: dict[int, int] = {}
    g_score: List[float] = [float("inf")] * n
    g_score[start] = 0.0

    while open_heap:
        _, current_g, current = heapq.heappop(open_heap)

        if current == goal:
            # Reconstruct path.
            path: List[int] = [goal]
            while path[-1] != start:
                path.append(came_from[path[-1]])
            path.reverse()
            return path

        # Explore neighbours.
        for neighbor in range(n):
            weight = adj[current][neighbor]
            if weight == float("inf"):
                continue
            tentative_g = current_g + weight
            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_heap, (f_score, tentative_g, neighbor))

    # No path found.
    return []
