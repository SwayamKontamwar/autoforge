"""Tests for the model-response parser and its tolerance of messy LLM JSON."""

from __future__ import annotations

import json

import pytest

from builder.llm import ProviderError, parse_patch


def test_parse_patch_reads_marker_format() -> None:
    raw = (
        "SUMMARY: add reverse helper\n"
        "=== FILE: app/toolkit/textutil.py ===\n"
        "def reverse_words(text):\n"
        '    return " ".join(reversed(text.split()))\n'
        "=== FILE: tests/toolkit/test_textutil.py ===\n"
        "from app.toolkit.textutil import reverse_words\n\n\n"
        "def test_reverse():\n"
        '    assert reverse_words("a b c") == "c b a"\n'
        "=== END ==="
    )
    patch = parse_patch(raw)
    assert patch.summary == "add reverse helper"
    assert [f.path for f in patch.files] == [
        "app/toolkit/textutil.py",
        "tests/toolkit/test_textutil.py",
    ]
    # Raw quotes and no escaping survive verbatim — the whole point of the format.
    assert 'return " ".join(reversed(text.split()))' in patch.files[0].content


def test_parse_patch_marker_format_handles_quotes_and_backslashes() -> None:
    raw = (
        "SUMMARY: split on whitespace\n"
        "=== FILE: app/toolkit/x.py ===\n"
        "import re\n"
        'def f(t):\n'
        '    return re.split(r"\\s+", t)\n'
        "=== END ==="
    )
    patch = parse_patch(raw)
    # Both an unescaped double-quote and a regex backslash pass through untouched.
    assert 're.split(r"\\s+", t)' in patch.files[0].content


def test_parse_patch_reads_clean_json() -> None:
    raw = json.dumps(
        {"summary": "add thing", "files": [{"path": "app/a.py", "content": "x = 1\n"}]}
    )
    patch = parse_patch(raw)
    assert patch.summary == "add thing"
    assert patch.files[0].path == "app/a.py"
    assert patch.files[0].content == "x = 1\n"


def test_parse_patch_strips_code_fences() -> None:
    raw = '```json\n{"summary": "s", "files": [{"path": "app/a.py", "content": "y = 2\\n"}]}\n```'
    patch = parse_patch(raw)
    assert patch.files[0].content == "y = 2\n"


def test_parse_patch_repairs_unescaped_regex_backslashes() -> None:
    # A backslash in a regex (\s) is an invalid JSON escape; strict json.loads rejects it.
    raw = (
        '{"summary": "re", "files": [{"path": "app/a.py", '
        '"content": "import re\\ndef f(t):\\n    return re.split(r\'\\s+\', t)\\n"}]}'
    )
    with pytest.raises(json.JSONDecodeError):
        json.loads(raw)
    patch = parse_patch(raw)
    assert patch.files[0].path == "app/a.py"
    assert "\\s+" in patch.files[0].content  # the backslash survived intact


def test_parse_patch_repairs_literal_newlines_in_strings() -> None:
    # A model that pastes real newlines into "content" produces illegal control chars.
    raw = '{"summary": "nl", "files": [{"path": "app/a.py", "content": "line1\nline2\n"}]}'
    with pytest.raises(json.JSONDecodeError):
        json.loads(raw)
    patch = parse_patch(raw)
    assert patch.files[0].content == "line1\nline2\n"


def test_parse_patch_rejects_hopeless_input() -> None:
    with pytest.raises(ProviderError):
        parse_patch("this is not JSON at all")
