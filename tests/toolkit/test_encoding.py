import pytest

from app.toolkit.encoding import base62_decode, base62_encode


def test_base62_encode_basic_cases() -> None:
    assert base62_encode(0) == "0"
    assert base62_encode(125) == "21"
    # 62^2 - 1 = 3843 should encode to "ZZ"
    assert base62_encode(3843) == "ZZ"


def test_base62_encode_negative_raises() -> None:
    with pytest.raises(ValueError):
        base62_encode(-1)


def test_base62_decode_basic_cases() -> None:
    assert base62_decode("0") == 0
    assert base62_decode("21") == 125
    # 62^2 - 1 = 3843 should decode from "ZZ"
    assert base62_decode("ZZ") == 3843


def test_base62_decode_edge_cases() -> None:
    # Empty string is invalid.
    with pytest.raises(ValueError):
        base62_decode("")
    # Non‑string input raises TypeError.
    with pytest.raises(TypeError):
        base62_decode(123)  # type: ignore[arg-type]
    # Invalid character raises ValueError.
    with pytest.raises(ValueError):
        base62_decode("!@#")
