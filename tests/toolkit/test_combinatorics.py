import pytest

from app.toolkit.combinatorics import multinomial, nth_permutation, permutation_index


def test_nth_permutation_typical() -> None:
    seq = [1, 2, 3]
    assert nth_permutation(seq, 0) == [1, 2, 3]
    assert nth_permutation(seq, 1) == [1, 3, 2]
    assert nth_permutation(seq, 4) == [3, 1, 2]


def test_nth_permutation_edge_cases() -> None:
    # Empty sequence returns empty list for n == 0
    assert nth_permutation([], 0) == []

    # Out‑of‑range index raises ValueError
    with pytest.raises(ValueError):
        nth_permutation([1, 2], 2)  # only two permutations: indices 0 and 1


def test_permutation_index_typical() -> None:
    seq = [1, 2, 3]
    # Verify round‑trip relationship with nth_permutation
    for idx in range(6):
        perm = nth_permutation(seq, idx)
        assert permutation_index(seq, perm) == idx


def test_permutation_index_edge_cases() -> None:
    # Empty sequence
    assert permutation_index([], []) == 0

    # Invalid permutation raises ValueError
    with pytest.raises(ValueError):
        permutation_index([1, 2, 3], [1, 2])  # length mismatch

    with pytest.raises(ValueError):
        permutation_index([1, 2, 3], [1, 1, 2])  # duplicate / missing items


def test_multinomial_typical() -> None:
    # Multinomial coefficient for counts [2, 1, 1] => 4! / (2! * 1! * 1!) = 12
    assert multinomial([2, 1, 1]) == 12


def test_multinomial_edge_cases() -> None:
    # Empty counts should return 1
    assert multinomial([]) == 1

    # Negative count should raise ValueError
    with pytest.raises(ValueError):
        multinomial([1, -1, 2])
