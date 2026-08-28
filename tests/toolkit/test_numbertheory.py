import pytest

from app.toolkit.numbertheory import euler_totient, mobius


def test_euler_totient_typical() -> None:
    cases = {
        1: 1,
        2: 1,
        5: 4,
        9: 6,
        10: 4,
        13: 12,
        100: 40,
    }
    for n, expected in cases.items():
        assert euler_totient(n) == expected


def test_euler_totient_edge_cases() -> None:
    with pytest.raises(ValueError):
        euler_totient(0)
    with pytest.raises(ValueError):
        euler_totient(-7)


def test_mobius_typical() -> None:
    cases = {
        1: 1,
        2: -1,
        3: -1,
        4: 0,
        5: -1,
        6: 1,
        7: -1,
        8: 0,
        9: 0,
        10: 1,
        30: -1,
        210: 1,
    }
    for n, expected in cases.items():
        assert mobius(n) == expected


def test_mobius_edge_cases() -> None:
    with pytest.raises(ValueError):
        mobius(0)
    with pytest.raises(ValueError):
        mobius(-3)
