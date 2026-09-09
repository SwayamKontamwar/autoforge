import pytest

from app.toolkit.mathx import deg_normalize


@pytest.mark.parametrize(
    "input_deg,expected",
    [
        (0, 0),
        (360, 0),
        (-45, 315),
        (720, 0),
        (450, 90),
        (30.5, 30.5),
        (-0.0, 0.0),
        (1e6, 1e6 % 360),
    ],
)
def test_deg_normalize_various_cases(input_deg, expected):
    assert deg_normalize(input_deg) == pytest.approx(expected)
