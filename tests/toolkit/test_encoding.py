import pytest

from app.toolkit.encoding import base62_encode


def test_base62_encode_basic_cases() -> None:
    assert base62_encode(0) == "0"
    assert base62_encode(125) == "21"
    # 62^2 - 1 = 3843 should encode to "ZZ"
    assert base62_encode(3843) == "ZZ"


def test_base62_encode_negative_raises() -> None:
    with pytest.raises(ValueError):
        base62_encode(-1)
