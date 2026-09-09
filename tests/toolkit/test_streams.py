import itertools

import pytest

from app.toolkit.streams import batched, iterate, repeat_each


def test_batched_basic() -> None:
    result = list(batched([1, 2, 3, 4, 5], 2))
    assert result == [(1, 2), (3, 4), (5,)]


def test_batched_n_larger_than_iterable() -> None:
    result = list(batched("abc", 5))
    assert result == [("a", "b", "c")]


def test_batched_invalid_n() -> None:
    with pytest.raises(ValueError):
        list(batched([1, 2, 3], 0))


def test_iterate_basic() -> None:
    # Generate powers of two starting from 1, take first 5 values.
    seq = itertools.islice(iterate(1, lambda x: x * 2), 5)
    assert list(seq) == [1, 2, 4, 8, 16]


def test_iterate_identity_edge_case() -> None:
    # Identity function should repeat the start value indefinitely.
    seq = itertools.islice(iterate("a", lambda x: x), 3)
    assert list(seq) == ["a", "a", "a"]


def test_repeat_each_basic() -> None:
    result = list(repeat_each([1, 2, 3], 2))
    assert result == [1, 1, 2, 2, 3, 3]


def test_repeat_each_n_one_returns_original() -> None:
    original = [4, 5, 6]
    result = list(repeat_each(original, 1))
    assert result == original


def test_repeat_each_invalid_n() -> None:
    with pytest.raises(ValueError):
        list(repeat_each([1, 2], 0))
