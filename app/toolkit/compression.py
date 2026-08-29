"""Run‑length encoding utilities for bytes.

The primary function, :func:`rle_bytes_encode`, compresses a ``bytes`` object
using a simple run‑length encoding scheme where each run is represented by a
pair of bytes: ``<count><value>``. ``count`` is stored as a single unsigned byte
(0‑255). Runs longer than 255 are split into multiple pairs.

Example
-------
>>> rle_bytes_encode(b\"\\x01\\x01\\x01\\x02\\x02\\x03\")
b'\\x03\\x01\\x02\\x02\\x01\\x03'
"""

from __future__ import annotations

from typing import List


def rle_bytes_encode(data: bytes) -> bytes:
    """Encode *data* using run‑length encoding.

    The encoding format is a sequence of ``<count><byte>`` pairs, where
    ``count`` is a single byte representing the number of consecutive
    occurrences of ``byte`` (1‑255). If a run exceeds 255, it is split into
    multiple pairs.

    Args:
        data: The bytes object to encode.

    Returns:
        A new ``bytes`` object containing the RLE representation.
    """
    if not data:
        return b""

    encoded_parts: List[int] = []
    current_byte = data[0]
    count = 1

    for b in data[1:]:
        if b == current_byte and count < 255:
            count += 1
        else:
            # Flush the current run
            encoded_parts.append(count)
            encoded_parts.append(current_byte)
            # Start new run
            current_byte = b
            count = 1

    # Flush the final run
    encoded_parts.append(count)
    encoded_parts.append(current_byte)

    return bytes(encoded_parts)


def rle_bytes_decode(data: bytes) -> bytes:
    """Decode *data* from run‑length encoding back to the original bytes.

    The input must consist of an even number of bytes, each pair representing
    ``<count><value>``. ``count`` must be in the range 1‑255; a ``ValueError`` is
    raised for malformed input.

    Args:
        data: The RLE‑encoded bytes.

    Returns:
        The original uncompressed ``bytes`` object.

    Raises:
        ValueError: If *data* has an odd length.
    """
    if not data:
        return b""

    if len(data) % 2 != 0:
        raise ValueError("Encoded data length must be even")

    decoded = bytearray()
    for i in range(0, len(data), 2):
        count = data[i]
        value = data[i + 1]
        decoded.extend([value] * count)

    return bytes(decoded)
