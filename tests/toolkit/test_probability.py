import math

import pytest

from app.toolkit.probability import binomial_pmf, poisson_pmf


def test_binomial_pmf_typical() -> None:
    # 10 trials, 3 successes, p=0.5
    n, k, p = 10, 3, 0.5
    expected = math.comb(n, k) * (p**k) * ((1 - p) ** (n - k))
    assert binomial_pmf(k, n, p) == pytest.approx(expected, rel=1e-12)


def test_binomial_pmf_edge_cases() -> None:
    # Zero trials, zero successes should be probability 1
    assert binomial_pmf(0, 0, 0.3) == 1.0
    # Probability 0 with k>0 yields 0
    assert binomial_pmf(1, 5, 0.0) == 0.0
    # Probability 1 with k<n yields 0
    assert binomial_pmf(2, 5, 1.0) == 0.0
    # Probability 1 with k=n yields 1
    assert binomial_pmf(5, 5, 1.0) == 1.0


def test_binomial_pmf_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        binomial_pmf(-1, 5, 0.5)  # negative k
    with pytest.raises(ValueError):
        binomial_pmf(6, 5, 0.5)  # k > n
    with pytest.raises(ValueError):
        binomial_pmf(2, -3, 0.5)  # negative n
    with pytest.raises(ValueError):
        binomial_pmf(2, 5, -0.1)  # p out of range
    with pytest.raises(ValueError):
        binomial_pmf(2, 5, 1.2)  # p out of range


def test_poisson_pmf_typical() -> None:
    # λ = 3, k = 2 → e⁻³ * 3² / 2!
    lam, k = 3.0, 2
    expected = math.exp(-lam) * (lam**k) / math.factorial(k)
    assert poisson_pmf(k, lam) == pytest.approx(expected, rel=1e-12)


def test_poisson_pmf_edge_cases() -> None:
    # λ = 0, k = 0 → 1
    assert poisson_pmf(0, 0.0) == 1.0
    # λ = 0, k > 0 → 0
    assert poisson_pmf(5, 0.0) == 0.0


def test_poisson_pmf_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        poisson_pmf(-1, 2.0)  # negative k
    with pytest.raises(ValueError):
        poisson_pmf(2.5, 2.0)  # non‑int k
    with pytest.raises(ValueError):
        poisson_pmf(2, -1.0)  # negative λ
    with pytest.raises(ValueError):
        poisson_pmf(2, "lam")  # non‑numeric λ
