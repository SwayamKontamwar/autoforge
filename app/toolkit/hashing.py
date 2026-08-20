"""Hashing utilities for the autoforge toolkit.

Provides functions for common cryptographic hash operations.
"""

from __future__ import annotations

import hashlib
from typing import Final

__all__: Final = ["md5_hex", "sha256_hex"]


def md5_hex(data: bytes) -> str:
    """Return the MD5 hex digest of *data*.

    Args:
        data: Bytes-like object to hash.

    Returns:
        A 32‑character hexadecimal string representing the MD5 digest.

    Raises:
        TypeError: If *data* is not a ``bytes``‑like object.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("md5_hex expects a bytes-like object")
    return hashlib.md5(data).hexdigest()


def sha256_hex(data: bytes) -> str:
    """Return the SHA‑256 hex digest of *data*.

    Args:
        data: Bytes-like object to hash.

    Returns:
        A 64‑character hexadecimal string representing the SHA‑256 digest.

    Raises:
        TypeError: If *data* is not a ``bytes``‑like object.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("sha256_hex expects a bytes-like object")
    return hashlib.sha256(data).hexdigest()
