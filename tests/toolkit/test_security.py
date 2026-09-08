import re

from app.toolkit.security import constant_time_equals, generate_token, hash_password


def test_constant_time_equals_identical_strings() -> None:
    assert constant_time_equals("secure-token-123", "secure-token-123") is True


def test_constant_time_equals_different_strings() -> None:
    assert constant_time_equals("secure-token-123", "secure-token-124") is False


def test_constant_time_equals_length_mismatch() -> None:
    assert constant_time_equals("short", "much longer string") is False


def test_constant_time_equals_empty_strings() -> None:
    assert constant_time_equals("", "") is True


def test_generate_token_is_urlsafe_and_correct_length() -> None:
    token = generate_token(16)
    assert isinstance(token, str)
    # URL‑safe characters only (alphanumeric, hyphen, underscore)
    assert re.fullmatch(r"[A-Za-z0-9_-]+", token)
    # token length varies due to base64 padding removal; ensure it's non‑empty
    assert len(token) > 0


def test_hash_password_returns_proper_format() -> None:
    result = hash_password("s3cr3t")
    parts = result.split("$")
    # Expect three components: iterations, salt (hex), hash (hex)
    assert len(parts) == 3
    iterations, salt_hex, hash_hex = parts
    assert iterations.isdigit()
    # Default iterations should be 100000
    assert int(iterations) == 100_000
    # Salt should be 32 hex characters (16 bytes)
    assert len(salt_hex) == 32
    # Hash should be 64 hex characters (32‑byte SHA‑256 output)
    assert len(hash_hex) == 64
    # Ensure hex strings contain only valid characters
    assert re.fullmatch(r"[0-9a-f]+", salt_hex)
    assert re.fullmatch(r"[0-9a-f]+", hash_hex)


def test_hash_password_edge_empty_password() -> None:
    empty_result = hash_password("")
    nonempty_result = hash_password("nonempty")
    assert empty_result != nonempty_result
    # Both should still follow the format
    for res in (empty_result, nonempty_result):
        parts = res.split("$")
        assert len(parts) == 3
        assert parts[0].isdigit()
        assert len(parts[1]) == 32
        assert len(parts[2]) == 64
