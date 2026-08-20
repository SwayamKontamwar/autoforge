import pytest

from app.toolkit.hashing import md5_hex, sha256_hex


def test_md5_hex_basic() -> None:
    assert md5_hex(b"hello") == "5d41402abc4b2a76b9719d911017c592"


def test_md5_hex_empty() -> None:
    assert md5_hex(b"") == "d41d8cd98f00b204e9800998ecf8427e"


def test_md5_hex_invalid_type() -> None:
    with pytest.raises(TypeError):
        md5_hex("not bytes")  # type: ignore


def test_sha256_hex_basic() -> None:
    assert (
        sha256_hex(b"hello") == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_sha256_hex_empty() -> None:
    assert sha256_hex(b"") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_sha256_hex_invalid_type() -> None:
    with pytest.raises(TypeError):
        sha256_hex(123)  # type: ignore
