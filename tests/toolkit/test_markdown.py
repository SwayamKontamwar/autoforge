from app.toolkit.markdown import md_bold


def test_md_bold_typical() -> None:
    assert md_bold("hello") == "**hello**"
    assert md_bold("  spaced  ") == "**  spaced  **"


def test_md_bold_edge_cases() -> None:
    # Empty string should still be wrapped in bold markers
    assert md_bold("") == "****"
    # Text containing asterisks is not altered, just wrapped
    assert md_bold("*star*") == "***star***"
