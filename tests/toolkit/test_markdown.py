from app.toolkit.markdown import md_bold, md_italic


def test_md_bold_typical() -> None:
    assert md_bold("hello") == "**hello**"
    assert md_bold("  spaced  ") == "**  spaced  **"


def test_md_bold_edge_cases() -> None:
    # Empty string should still be wrapped in bold markers
    assert md_bold("") == "****"
    # Text containing asterisks is not altered, just wrapped
    assert md_bold("*star*") == "***star***"


def test_md_italic_typical() -> None:
    assert md_italic("hello") == "*hello*"
    assert md_italic("  spaced  ") == "*  spaced  *"


def test_md_italic_edge_cases() -> None:
    # Empty string should still be wrapped in italic markers
    assert md_italic("") == "**"
    # Text containing asterisks is wrapped, resulting in doubled asterisks at edges
    assert md_italic("*star*") == "**star**"
