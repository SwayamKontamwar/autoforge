import pytest

from app.toolkit.compression import rle_bytes_decode, rle_bytes_encode


def test_rle_bytes_encode_basic() -> None:
    data = b"\x01\x01\x01\x02\x02\x03"
    # Expected: 3×0x01, 2×0x02, 1×0x03 -> b'\x03\x01\x02\x02\x01\x03'
    expected = b"\x03\x01\x02\x02\x01\x03"
    assert rle_bytes_encode(data) == expected


def test_rle_bytes_encode_empty() -> None:
    assert rle_bytes_encode(b"") == b""


def test_rle_bytes_encode_long_run() -> None:
    # 300 consecutive 0xAA bytes should be split into 255 and 45.
    data = b"\xaa" * 300
    expected = bytes([255, 0xAA, 45, 0xAA])
    assert rle_bytes_encode(data) == expected


def test_rle_bytes_decode_basic() -> None:
    encoded = b"\x03\x01\x02\x02\x01\x03"
    expected = b"\x01\x01\x01\x02\x02\x03"
    assert rle_bytes_decode(encoded) == expected


def test_rle_bytes_decode_empty() -> None:
    assert rle_bytes_decode(b"") == b""


def test_rle_bytes_decode_roundtrip() -> None:
    data = b"\xaa" * 300
    encoded = rle_bytes_encode(data)
    assert rle_bytes_decode(encoded) == data


def test_rle_bytes_decode_malformed() -> None:
    # Odd length should raise ValueError
    with pytest.raises(ValueError):
        rle_bytes_decode(b"\x03")
