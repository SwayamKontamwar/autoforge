import pytest

from app.toolkit.combinatorics import nth_permutation


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
