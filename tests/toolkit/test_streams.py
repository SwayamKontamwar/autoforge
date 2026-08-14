import pytest

from app.toolkit.streams import batched


def test_batched_basic() -> None:
    result = list(batched([1, 2, 3, 4, 5], 2))
    assert result == [(1, 2), (3, 4), (5,)]


def test_batched_n_larger_than_iterable() -> None:
    result = list(batched("abc", 5))
    assert result == [("a", "b", "c")]


def test_batched_invalid_n() -> None:
    with pytest.raises(ValueError):
        list(batched([1, 2, 3], 0))
