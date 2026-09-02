import pytest

from app.toolkit.encoding import (
    base58_encode,
    base62_decode,
    base62_encode,
)


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


def test_base58_encode_basic_cases() -> None:
    # Zero maps to '1' in Bitcoin base58.
    assert base58_encode(0) == "1"
    # 57 should map to the last character 'z'.
    assert base58_encode(57) == "z"
    # 58 should be '21' (1*58 + 0).
    assert base58_encode(58) == "21"


def test_base58_encode_invalid_input() -> None:
    with pytest.raises(ValueError):
        base58_encode(-5)
    with pytest.raises(TypeError):
        base58_encode("not an int")  # type: ignore[arg-type]
