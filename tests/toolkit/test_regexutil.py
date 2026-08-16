from app.toolkit.regexutil import extract_emails


def test_extract_emails_typical() -> None:
    text = "Please contact support@example.com or sales@example.co.uk for assistance."
    result = extract_emails(text)
    assert result == ["support@example.com", "sales@example.co.uk"]


def test_extract_emails_edge_cases() -> None:
    # Email followed by punctuation should not include the punctuation.
    text = "Reach us at user.name+tag@example.com, or at admin@sub.domain.org."
    result = extract_emails(text)
    assert result == ["user.name+tag@example.com", "admin@sub.domain.org"]

    # No email addresses present
    assert extract_emails("No contacts here.") == []
