import pytest

from app.toolkit.finance import compound_interest


def test_compound_interest_typical() -> None:
    # 5 % annual rate, 3 years, principal 1000 → 1157.625
    result = compound_interest(1000, 0.05, 3)
    assert result == pytest.approx(1157.625, rel=1e-9)


def test_compound_interest_edge_cases() -> None:
    # Zero periods returns the principal unchanged
    assert compound_interest(500, 0.07, 0) == 500.0
    # Zero rate leaves principal unchanged regardless of periods
    assert compound_interest(250, 0.0, 10) == 250.0
    # Negative principal is allowed (e.g., debt)
    assert compound_interest(-100, 0.1, 2) == pytest.approx(-121.0, rel=1e-9)
    # Negative rate (deflation) reduces the amount
    assert compound_interest(200, -0.05, 2) == pytest.approx(180.5, rel=1e-9)
