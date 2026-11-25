import pytest

from app.toolkit.probability import expected_value


def test_expected_value_typical() -> None:
    outcomes = [0, 1, 2]
    probs = [0.2, 0.5, 0.3]
    assert expected_value(outcomes, probs) == pytest.approx(1.1, rel=1e-12)


def test_expected_value_mismatched_lengths() -> None:
    with pytest.raises(ValueError):
        expected_value([0, 1], [0.5])  # lengths differ


def test_expected_value_invalid_probability_sum() -> None:
    with pytest.raises(ValueError):
        expected_value([0, 1], [0.4, 0.4])  # sums to 0.8, not 1


def test_expected_value_empty() -> None:
    assert expected_value([], []) == 0.0
