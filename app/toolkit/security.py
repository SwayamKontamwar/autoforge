"""Security‑related helper utilities.

This module currently provides a constant‑time string comparison function to
mitigate timing attacks when checking secrets such as tokens or passwords.
"""

from __future__ import annotations

import itertools
import secrets
from typing import Iterable


def _iter_bytes(s: str) -> Iterable[int]:
    """Yield integer byte values for the given string.

    The function encodes the string as UTF‑8 and yields each byte as an int.
    This ensures that multi‑byte Unicode characters are compared byte‑wise,
    matching the behaviour of typical constant‑time implementations that work
    on ``bytes`` objects.
    """
    return s.encode("utf-8")


def constant_time_equals(a: str, b: str) -> bool:
    """Return ``True`` if *a* and *b* are equal, ``False`` otherwise.

    The comparison is performed in constant time with respect to the length of
    the inputs: the runtime does not short‑circuit on the first differing
    character and does not depend on the position of a mismatch.

    Args:
        a: First string.
        b: Second string.

    Returns:
        ``True`` if the strings are identical, ``False`` otherwise.
    """
    # Convert to bytes for a byte‑wise comparison.
    a_bytes = _iter_bytes(a)
    b_bytes = _iter_bytes(b)

    # Start with the XOR of the lengths; any length mismatch will set a bit.
    result = len(a.encode("utf-8")) ^ len(b.encode("utf-8"))

    # Iterate over the longest sequence, using 0 as the fill value for the
    # shorter one. This guarantees the loop runs the same number of iterations
    # regardless of length differences.
    for x, y in itertools.zip_longest(a_bytes, b_bytes, fillvalue=0):
        result |= x ^ y

    return result == 0


def generate_token(byte_length: int) -> str:
    """Generate a URL‑safe secret token.

    The token contains ``byte_length`` bytes of randomness, encoded using a
    URL‑safe base64 variant (the same algorithm used by :func:`secrets.token_urlsafe`).

    Args:
        byte_length: Number of random bytes to include in the token. Must be
            a positive integer.

    Returns:
        A URL‑safe string token.

    Raises:
        ValueError: If ``byte_length`` is not a positive integer.
    """
    if not isinstance(byte_length, int) or byte_length <= 0:
        raise ValueError("byte_length must be a positive integer")
    # ``secrets.token_urlsafe`` returns a string with the requested amount of
    # randomness, URL‑safe, and without padding.
    return secrets.token_urlsafe(byte_length)
