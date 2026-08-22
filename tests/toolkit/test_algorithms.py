from app.toolkit.algorithms import binary_search, bisect_left


def test_binary_search_found() -> None:
    data = [1, 3, 5, 7, 9]
    assert binary_search(data, 5) == 2
    assert binary_search(data, 1) == 0
    assert binary_search(data, 9) == 4


def test_binary_search_not_found() -> None:
    data = [2, 4, 6, 8]
    assert binary_search(data, 5) == -1
    assert binary_search([], 1) == -1


def test_binary_search_edge_cases() -> None:
    # Single-element list
    assert binary_search([42], 42) == 0
    assert binary_search([42], 0) == -1


def test_bisect_left_typical_and_duplicates() -> None:
    data = [1, 2, 2, 2, 3]
    # Leftmost insertion point for existing value
    assert bisect_left(data, 2) == 1
    # Insertion point for a value not present
    assert bisect_left(data, 4) == 5
    # Insertion point at start
    assert bisect_left(data, 0) == 0
    # Insertion point at end when greater than all
    assert bisect_left([1, 3, 5], 6) == 3


def test_bisect_left_edge_cases() -> None:
    # Empty list returns 0
    assert bisect_left([], 10) == 0
    # All elements equal to target
    assert bisect_left([5, 5, 5], 5) == 0
    # Target less than all elements
    assert bisect_left([10, 20, 30], 5) == 0
