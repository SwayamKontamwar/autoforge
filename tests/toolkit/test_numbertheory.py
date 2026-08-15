import pytest

from app.toolkit.numbertheory import euler_totient


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
