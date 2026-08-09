from app.toolkit import is_email


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
