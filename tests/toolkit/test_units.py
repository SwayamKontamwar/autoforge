import pytest

from app.toolkit.units import (
    celsius_to_fahrenheit,
    celsius_to_kelvin,
    fahrenheit_to_celsius,
)


def test_celsius_to_fahrenheit_basic() -> None:
    assert celsius_to_fahrenheit(0) == 32.0
    assert celsius_to_fahrenheit(100) == 212.0


def test_celsius_to_fahrenheit_edge_cases() -> None:
    # -40°C is the point where Celsius and Fahrenheit are equal
    assert celsius_to_fahrenheit(-40) == -40.0
    # Test with a typical body temperature conversion
    result = celsius_to_fahrenheit(37.7778)
    assert result == pytest.approx(100.0, rel=1e-5)


def test_fahrenheit_to_celsius_basic() -> None:
    assert fahrenheit_to_celsius(32) == 0.0
    assert fahrenheit_to_celsius(212) == 100.0


def test_fahrenheit_to_celsius_edge_cases() -> None:
    # -40°F equals -40°C
    assert fahrenheit_to_celsius(-40) == -40.0
    # Test conversion with a non‑integer result
    result = fahrenheit_to_celsius(98.6)
    assert result == pytest.approx(37.0, rel=1e-5)


def test_celsius_to_kelvin_basic() -> None:
    assert celsius_to_kelvin(0) == pytest.approx(273.15)
    assert celsius_to_kelvin(100) == pytest.approx(373.15)


def test_celsius_to_kelvin_edge_cases() -> None:
    # Absolute zero in Celsius corresponds to 0 K
    assert celsius_to_kelvin(-273.15) == pytest.approx(0.0)
    # Negative temperature conversion
    assert celsius_to_kelvin(-40) == pytest.approx(233.15)
