import pytest

from app.toolkit.collections import chunk


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
