from app.toolkit import is_email, is_ipv6, is_url


def test_is_email_valid_cases() -> None:
    assert is_email("user@example.com")
    assert is_email("john.doe+tag@sub.example.co.uk")
    assert is_email("a_b-c.d@domain.io")


def test_is_email_invalid_cases() -> None:
    assert not is_email("plainaddress")
    assert not is_email("missing-at-sign.com")
    assert not is_email("user@.invalid.com")
    assert not is_email("")
    assert not is_email(123)  # type: ignore[arg-type]


def test_is_url_valid_cases() -> None:
    assert is_url("http://example.com")
    assert is_url("https://sub.domain.org/path?query=1")
    assert is_url("https://example.com:8080")
    # URL with user info is still considered valid for scheme/host presence
    assert is_url("http://user:pass@example.com")


def test_is_url_invalid_cases() -> None:
    assert not is_url("ftp://example.com")
    assert not is_url("http:/example.com")
    assert not is_url("://missing.scheme.com")
    assert not is_url("")
    assert not is_url(None)  # type: ignore[arg-type]


def test_is_ipv6_valid_cases() -> None:
    # Full notation
    assert is_ipv6("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
    # Compressed notation
    assert is_ipv6("2001:db8::1")
    # Loopback
    assert is_ipv6("::1")
    # Link‑local
    assert is_ipv6("fe80::")
    # IPv4‑mapped address
    assert is_ipv6("::ffff:192.0.2.128")


def test_is_ipv6_invalid_cases() -> None:
    # Too many colons
    assert not is_ipv6("2001:db8:::1")
    # Invalid hex digit
    assert not is_ipv6("2001:db8::g")
    # Too many groups
    assert not is_ipv6("2001:db8:85a3:0000:0000:8a2e:0370:7334:1234")
    # Empty string
    assert not is_ipv6("")
    # Non‑string input
    assert not is_ipv6(123)  # type: ignore[arg-type]
