"""Utility functions for unit conversions.

Currently provides temperature conversion from Celsius to Fahrenheit.
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
