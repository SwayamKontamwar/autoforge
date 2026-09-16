import math

from app.toolkit.graphx import astar, floyd_warshall


def test_floyd_warshall_basic() -> None:
    INF = math.inf
    graph = [
        [0, 3, INF, 7],
        [8, 0, 2, INF],
        [5, INF, 0, 1],
        [2, INF, INF, 0],
    ]
    result = floyd_warshall(graph)

    # shortest paths known from classic Floyd‑Warshall example
    assert result[0][2] == 5  # 0 → 1 → 2
    assert result[1][3] == 3  # 1 → 2 → 3
    assert result[3][1] == 5  # 3 → 0 → 1


def test_floyd_warshall_edge_cases() -> None:
    # empty graph
    assert floyd_warshall([]) == []

    # single‑node graph
    assert floyd_warshall([[0]]) == [[0]]

    INF = math.inf
    # graph with no edges
    graph = [
        [0, INF],
        [INF, 0],
    ]
    result = floyd_warshall(graph)
    assert result == [[0, INF], [INF, 0]]


def test_astar_basic_path() -> None:
    INF = math.inf
    graph = [
        [0, 3, INF, INF],
        [INF, 0, 2, INF],
        [INF, INF, 0, 1],
        [INF, INF, INF, 0],
    ]
    # Shortest path from 0 to 3 is 0 → 1 → 2 → 3 with total weight 6
    path = astar(graph, start=0, goal=3)
    assert path == [0, 1, 2, 3]


def test_astar_no_path_and_self() -> None:
    INF = math.inf
    graph = [
        [0, INF],
        [INF, 0],
    ]
    # No path between distinct nodes
    assert astar(graph, start=0, goal=1) == []

    # Path from a node to itself
    assert astar(graph, start=1, goal=1) == [1]
