from app.toolkit.algorithms import binary_search


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
