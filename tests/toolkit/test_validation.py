from app.toolkit import is_email, is_url


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
    assert not is_url("http:/invalid.com")
    assert not is_url("://missing-scheme.com")
    assert not is_url("http://")  # missing host
    assert not is_url("")
    assert not is_url(42)  # type: ignore[arg-type]
