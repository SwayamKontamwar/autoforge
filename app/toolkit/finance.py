"""Financial utilities.

Provides functions for common financial calculations. Currently includes:

- ``compound_interest``: Compute future value of a principal amount with
  compound interest applied at a fixed rate per period.
"""

from __future__ import annotations

from typing import Union

Number = Union[int, float]


def compound_interest(principal: Number, rate: Number, periods: int) -> float:
    """Return the future value of *principal* after *periods* compounding periods.

    The *rate* is expressed as a decimal (e.g., ``0.05`` for 5 %). The interest
    compounds once per period, so the formula is::

        FV = principal * (1 + rate) ** periods

    Args:
        principal: The initial amount of money. May be zero or negative.
        rate: Interest rate per period as a decimal. Zero is allowed.
        periods: Number of compounding periods. Must be a non‑negative integer.

    Returns:
        The future value as a ``float``.

    Raises:
        ValueError: If *periods* is negative.
    """
    if periods < 0:
        raise ValueError("periods must be a non‑negative integer")
    # Convert to float to avoid integer overflow and ensure fractional rates work.
    return float(principal) * (1.0 + float(rate)) ** periods
