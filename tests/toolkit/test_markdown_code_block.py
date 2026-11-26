from app.toolkit.markdown import md_code_block


def test_md_code_block_typical() -> None:
    code = "print('hi')"
    language = "python"
    expected = "```python\nprint('hi')\n```"
    assert md_code_block(code, language) == expected


def test_md_code_block_edge_cases() -> None:
    # Empty text and language
    assert md_code_block("", "") == "```\n\n```"
    # Language with surrounding whitespace should be trimmed
    assert md_code_block("x = 1", "  python  ") == "```python\nx = 1\n```"
