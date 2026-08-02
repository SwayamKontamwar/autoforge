"""Tests for the model-response parser and its tolerance of messy LLM JSON."""

from __future__ import annotations

import json
import urllib.error

import pytest

from builder import llm
from builder.llm import ProviderError, parse_patch


class _FakeResponse:
    """Minimal stand-in for the object urlopen returns as a context manager."""

    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> bool:
        return False


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


class _FakeHTTPError(urllib.error.HTTPError):
    def __init__(self, code: int, headers: dict | None = None) -> None:
        super().__init__("http://x", code, "err", headers or {}, None)

    def read(self) -> bytes:  # the real class reads from a file object we don't have
        return b"rate limited"


def test_rate_limit_is_waited_out_not_treated_as_an_outage(monkeypatch) -> None:
    """A free-tier key is metered per minute; a 429 is a pause, not a dead provider.

    One code-generation call can use most of a minute's budget once reasoning tokens
    count, so this fires in normal operation. Treating it as an outage would skip the
    run and leave the task untouched until the next schedule.
    """
    calls = {"n": 0}
    slept: list[float] = []

    def _urlopen(request, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise _FakeHTTPError(429, {"retry-after": "2"})
        return _FakeResponse({"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr(llm.urllib.request, "urlopen", _urlopen)
    monkeypatch.setattr(llm.time, "sleep", lambda s: slept.append(s))
    body = llm._post_with_rate_limit_retry(object())
    assert body["choices"][0]["message"]["content"] == "ok"
    assert calls["n"] == 2, "the request should have been retried"
    assert slept and slept[0] >= 2, "it must honour the provider's requested wait"


def test_rate_limit_eventually_gives_up_as_a_provider_error(monkeypatch) -> None:
    monkeypatch.setattr(
        llm.urllib.request, "urlopen",
        lambda request, timeout=None: (_ for _ in ()).throw(_FakeHTTPError(429)),
    )
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    with pytest.raises(llm.ProviderError):
        llm._post_with_rate_limit_retry(object())


def test_client_errors_are_not_retried(monkeypatch) -> None:
    """A bad key or model is permanent; retrying only burns the job's runtime."""
    calls = {"n": 0}

    def _urlopen(request, timeout=None):
        calls["n"] += 1
        raise _FakeHTTPError(401)

    monkeypatch.setattr(llm.urllib.request, "urlopen", _urlopen)
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    with pytest.raises(llm.ProviderError):
        llm._post_with_rate_limit_retry(object())
    assert calls["n"] == 1


def test_backoff_is_capped_so_a_job_cannot_hang(monkeypatch) -> None:
    assert llm._retry_after_seconds({"retry-after": "99999"}, 5.0) <= llm._MAX_BACKOFF_SECONDS
    assert llm._retry_after_seconds({}, 5.0) == 5.0
    assert llm._retry_after_seconds({"x-ratelimit-reset-tokens": "720ms"}, 5.0) >= 1.0
