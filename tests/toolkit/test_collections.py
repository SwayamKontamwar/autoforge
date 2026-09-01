import pytest

from app.toolkit.collections import chunk, flatten, flatten_deep


def test_chunk_basic() -> None:
    # Split a range of five numbers into chunks of size two.
    assert chunk(range(5), 2) == [[0, 1], [2, 3], [4]]


def test_chunk_empty_iterable() -> None:
    # An empty iterable yields an empty list of chunks.
    assert chunk([], 3) == []


def test_chunk_invalid_size() -> None:
    # Size must be a positive integer.
    with pytest.raises(ValueError):
        chunk([1, 2, 3], 0)


def test_flatten_basic() -> None:
    # Flatten one level of nesting, leaving strings intact.
    data = [1, [2, 3], (4, 5), "abc"]
    assert flatten(data) == [1, 2, 3, 4, 5, "abc"]


def test_flatten_edge_cases() -> None:
    # Empty iterable returns empty list.
    assert flatten([]) == []
    # Nested empty containers are ignored.
    assert flatten([[], [1], (), (2, 3)]) == [1, 2, 3]
    # Strings are not treated as iterables to flatten.
    assert flatten(["hi", ["there"]]) == ["hi", "there"]


def test_flatten_deep_basic() -> None:
    # Deeply nested structures are fully flattened.
    data = [1, [2, [3, [4]], 5], (6, 7), "xyz"]
    assert flatten_deep(data) == [1, 2, 3, 4, 5, 6, 7, "xyz"]


def test_flatten_deep_edge_cases() -> None:
    # Empty iterable returns empty list.
    assert flatten_deep([]) == []
    # Strings remain atomic even when nested.
    assert flatten_deep(["hi", ["there", ["!"]]]) == ["hi", "there", "!"]
