from app.toolkit.randomness import random_string


def test_random_string_length_and_charset() -> None:
    s = random_string(16)
    assert len(s) == 16
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    assert set(s).issubset(allowed)


def test_random_string_zero_and_negative_length() -> None:
    assert random_string(0) == ""
    assert random_string(-5) == ""
