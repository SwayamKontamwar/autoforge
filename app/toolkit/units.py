"""Utility functions for unit conversions.

Currently provides temperature conversion from Celsius to Fahrenheit and
other common unit conversions.
"""

from __future__ import annotations


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a temperature from Celsius to Fahrenheit.

    Args:
        celsius: Temperature in degrees Celsius.

    Returns:
        Temperature in degrees Fahrenheit.

    Example:
        >>> celsius_to_fahrenheit(0)
        32.0
        >>> celsius_to_fahrenheit(100)
        212.0
    """
    return celsius * 9.0 / 5.0 + 32.0


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert a temperature from Fahrenheit to Celsius.

    Args:
        fahrenheit: Temperature in degrees Fahrenheit.

    Returns:
        Temperature in degrees Celsius.

    Example:
        >>> fahrenheit_to_celsius(32)
        0.0
        >>> fahrenheit_to_celsius(212)
        100.0
    """
    return (fahrenheit - 32.0) * 5.0 / 9.0


def celsius_to_kelvin(celsius: float) -> float:
    """Convert a temperature from Celsius to Kelvin.

    Args:
        celsius: Temperature in degrees Celsius.

    Returns:
        Temperature in Kelvin.

    Example:
        >>> celsius_to_kelvin(0)
        273.15
    """
    return celsius + 273.15


def km_to_miles(kilometers: float) -> float:
    """Convert a distance from kilometres to miles.

    Args:
        kilometers: Distance in kilometres.

    Returns:
        Distance in miles.

    Example:
        >>> km_to_miles(1)
        0.62137119223733
    """
    return kilometers * 0.62137119223733


def meters_to_feet(meters: float) -> float:
    """Convert a distance from metres to feet.

    Args:
        meters: Distance in metres.

    Returns:
        Distance in feet.

    Example:
        >>> meters_to_feet(1)
        3.2808398950131235
    """
    return meters * 3.2808398950131235
