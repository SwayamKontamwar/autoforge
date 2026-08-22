from app.toolkit.randomness import random_hex, random_string


def test_random_string_length_and_charset() -> None:
    s = random_string(16)
    assert len(s) == 16
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    assert set(s).issubset(allowed)


def test_random_string_zero_and_negative_length() -> None:
    assert random_string(0) == ""
    assert random_string(-5) == ""


def test_random_hex_length_and_charset() -> None:
    token = random_hex(8)  # 8 bytes -> 16 hex chars
    assert len(token) == 16
    allowed = set("0123456789abcdef")
    assert set(token).issubset(allowed)


def test_random_hex_zero_and_negative_length() -> None:
    assert random_hex(0) == ""
    assert random_hex(-3) == ""
