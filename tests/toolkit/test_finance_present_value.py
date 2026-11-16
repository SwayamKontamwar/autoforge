import pytest

from app.toolkit.finance import present_value


def test_present_value_typical() -> None:
    # Future value 1157.625, 5 % rate, 3 periods → present value 1000
    pv = present_value(1157.625, 0.05, 3)
    assert pv == pytest.approx(1000.0, rel=1e-9)


def test_present_value_edge_cases() -> None:
    # Zero rate: present value equals future value regardless of periods
    assert present_value(500.0, 0.0, 10) == pytest.approx(500.0, rel=1e-9)
    # Zero periods: present value equals future value
    assert present_value(250.0, 0.07, 0) == pytest.approx(250.0, rel=1e-9)
