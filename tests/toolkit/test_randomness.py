from app.toolkit.randomness import random_hex, random_string, uuid4


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


def test_uuid4_format_and_version() -> None:
    uid = uuid4()
    # Standard UUID4 string length with hyphens is 36 characters
    assert len(uid) == 36
    # Hyphens at the correct positions
    assert uid[8] == uid[13] == uid[18] == uid[23] == "-"
    # Version character (position 14, zero‑based) must be '4'
    assert uid[14] == "4"
    # Variant bits (first character of the third group) must be one of 8, 9, a, b
    assert uid[19] in "89ab"


def test_uuid4_uniqueness() -> None:
    # Very low probability of collision; two successive calls should differ
    assert uuid4() != uuid4()
