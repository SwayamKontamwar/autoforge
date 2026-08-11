import pytest

from app.toolkit.units import celsius_to_fahrenheit


def test_celsius_to_fahrenheit_basic() -> None:
    assert celsius_to_fahrenheit(0) == 32.0
    assert celsius_to_fahrenheit(100) == 212.0


def test_celsius_to_fahrenheit_edge_cases() -> None:
    # -40°C is the point where Celsius and Fahrenheit are equal
    assert celsius_to_fahrenheit(-40) == -40.0
    # Test with a typical body temperature conversion
    result = celsius_to_fahrenheit(37.7778)
    assert result == pytest.approx(100.0, rel=1e-5)
