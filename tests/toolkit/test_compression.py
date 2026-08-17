from app.toolkit.compression import rle_bytes_encode


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
