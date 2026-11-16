"""Financial utilities.

Provides functions for common financial calculations. Currently includes:

- ``compound_interest``: Compute future value of a principal amount with
  compound interest applied at a fixed rate per period.
- ``monthly_payment``: Compute the fixed monthly payment for a loan given
  principal, annual interest rate, and term in years.
- ``present_value``: Discount a future amount back to its present value.
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
        periods: Number of compounding periods (must be non‑negative).

    Returns:
        The future value as a float.
    """
    if periods < 0:
        raise ValueError("periods must be non‑negative")
    return float(principal) * (1.0 + float(rate)) ** periods


def monthly_payment(principal: Number, annual_rate: Number, years: int) -> float:
    """Calculate the fixed monthly payment for a loan.

    Uses the standard amortizing loan formula::

        P = principal
        r = annual_rate / 12
        n = years * 12
        payment = P * r / (1 - (1 + r) ** -n)

    If *annual_rate* is zero, the payment is simply ``principal / n``.

    Args:
        principal: Loan amount.
        annual_rate: Annual interest rate as a decimal.
        years: Loan term in years (must be non‑negative).

    Returns:
        Monthly payment amount as a float.
    """
    if years < 0:
        raise ValueError("years must be non‑negative")
    months = years * 12
    if months == 0:
        raise ValueError("loan term must be at least one month")
    if annual_rate == 0:
        return float(principal) / months
    monthly_rate = float(annual_rate) / 12.0
    denominator = 1.0 - (1.0 + monthly_rate) ** -months
    return float(principal) * monthly_rate / denominator


def present_value(future_value: Number, rate: Number, periods: int) -> float:
    """Discount *future_value* back to its present value.

    The present value (PV) is computed as::

        PV = future_value / (1 + rate) ** periods

    Args:
        future_value: Amount to be received in the future.
        rate: Discount rate per period as a decimal.
        periods: Number of periods between now and the future value
                 (must be non‑negative).

    Returns:
        Present value as a float.
    """
    if periods < 0:
        raise ValueError("periods must be non‑negative")
    return float(future_value) / (1.0 + float(rate)) ** periods
