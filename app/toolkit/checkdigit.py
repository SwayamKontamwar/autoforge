"""Utility functions for calculating check digits.

This module currently provides a single function, ``upc_check_digit``, which
computes the check digit for a UPC‑A barcode according to the standard
algorithm:

1. Starting from the left, sum the digits in odd‑positioned places (1‑based
   indexing) and multiply the result by 3.
2. Add the sum of the digits in even‑positioned places.
3. The check digit is the amount required to round the total up to the next
   multiple of 10.  In formula form:

   ``check = (10 - (total % 10)) % 10``

The function accepts either a string or an integer representing the 11‑digit
payload (the check digit itself is *not* included).  A ``ValueError`` is raised
for inputs that are not exactly 11 decimal digits.

Additionally, this module now provides ``ean13_check_digit`` for EAN‑13 barcodes.
"""

from __future__ import annotations

from typing import Union


def upc_check_digit(upc: Union[str, int]) -> int:
    """Return the UPC‑A check digit for an 11‑digit code.

    Args:
        upc: The 11‑digit UPC payload as a string of digits or an integer.

    Returns:
        The check digit as an integer in the range 0‑9.

    Raises:
        ValueError: If ``upc`` does not consist of exactly 11 decimal digits.
    """
    # Normalise input to a string of digits
    upc_str = str(upc)
    if len(upc_str) != 11 or not upc_str.isdigit():
        raise ValueError("UPC must be exactly 11 decimal digits")

    # Compute sums of odd and even positioned digits (1‑based indexing)
    odd_sum = sum(int(upc_str[i]) for i in range(0, 11, 2))  # positions 1,3,5,...
    even_sum = sum(int(upc_str[i]) for i in range(1, 11, 2))  # positions 2,4,6,...

    total = (odd_sum * 3) + even_sum
    check_digit = (10 - (total % 10)) % 10
    return check_digit


def ean13_check_digit(ean: Union[str, int]) -> int:
    """Return the EAN‑13 check digit for a 12‑digit code.

    Args:
        ean: The 12‑digit EAN payload as a string of digits or an integer.

    Returns:
        The check digit as an integer in the range 0‑9.

    Raises:
        ValueError: If ``ean`` does not consist of exactly 12 decimal digits.
    """
    ean_str = str(ean)
    if len(ean_str) != 12 or not ean_str.isdigit():
        raise ValueError("EAN must be exactly 12 decimal digits")

    # Sum of digits in even positions (2,4,6,8,10,12) multiplied by 3
    even_sum = sum(int(ean_str[i]) for i in range(1, 12, 2))
    # Sum of digits in odd positions (1,3,5,7,9,11)
    odd_sum = sum(int(ean_str[i]) for i in range(0, 12, 2))

    total = (even_sum * 3) + odd_sum
    check_digit = (10 - (total % 10)) % 10
    return check_digit
