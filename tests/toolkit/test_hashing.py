import pytest

from app.toolkit.hashing import md5_hex


def test_md5_hex_basic() -> None:
    assert md5_hex(b"hello") == "5d41402abc4b2a76b9719d911017c592"


def test_md5_hex_empty() -> None:
    assert md5_hex(b"") == "d41d8cd98f00b204e9800998ecf8427e"


def test_md5_hex_invalid_type() -> None:
    with pytest.raises(TypeError):
        md5_hex("not bytes")  # type: ignore
