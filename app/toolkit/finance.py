"""Financial utilities.

Provides functions for common financial calculations. Currently includes:

- ``compound_interest``: Compute future value of a principal amount with
  compound interest applied at a fixed rate per period.
- ``monthly_payment``: Compute the fixed monthly payment for a loan given
  principal, annual interest rate, and term in years.
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


def monthly_payment(principal: Number, annual_rate: Number, years: int) -> float:
    """Return the fixed monthly payment for a loan.

    The calculation uses the standard amortizing loan formula::

        i = annual_rate / 12          # monthly interest rate (decimal)
        n = years * 12                # total number of payments
        payment = principal * i * (1 + i) ** n / ((1 + i) ** n - 1)

    If ``annual_rate`` is zero, the payment is simply ``principal / n``.

    Args:
        principal: Loan amount (may be negative for debt representation).
        annual_rate: Annual interest rate as a decimal (e.g., ``0.05`` for 5 %).
        years: Length of the loan in years. Must be a positive integer.

    Returns:
        The monthly payment as a ``float``.

    Raises:
        ValueError: If *years* is not a positive integer.
    """
    if years <= 0:
        raise ValueError("years must be a positive integer")
    n = years * 12
    i = float(annual_rate) / 12.0
    if i == 0.0:
        return float(principal) / n
    factor = (1.0 + i) ** n
    payment = float(principal) * i * factor / (factor - 1.0)
    return payment
