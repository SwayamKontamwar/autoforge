from app.toolkit.security import constant_time_equals


def test_constant_time_equals_identical_strings() -> None:
    assert constant_time_equals("secure-token-123", "secure-token-123") is True


def test_constant_time_equals_different_strings() -> None:
    assert constant_time_equals("secure-token-123", "secure-token-124") is False


def test_constant_time_equals_length_mismatch() -> None:
    assert constant_time_equals("short", "much longer string") is False


def test_constant_time_equals_empty_strings() -> None:
    assert constant_time_equals("", "") is True
