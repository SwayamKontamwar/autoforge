"""A successful HTTP status does not guarantee a JSON body.

Proxies, gateways and bot-protection layers all serve HTML interstitials with a
200, and a body can be truncated mid-character. If the decode error escapes, a
provider-side hiccup crashes the run instead of taking the outage path that logs
it and retries on the next schedule.
"""

from __future__ import annotations

import io
import urllib.request

import pytest

from builder import llm


class _FakeResponse(io.BytesIO):
    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc_info) -> bool:
        return False


def _serve(monkeypatch, body: bytes) -> None:
    monkeypatch.setattr(
        llm.urllib.request,
        "urlopen",
        lambda request, timeout=None: _FakeResponse(body),
    )


@pytest.mark.parametrize(
    "body",
    [
        b"<html><body>502 Bad Gateway</body></html>",
        b"",
        b'{"choices": [',
        b'{"a": "x\xe2\x80',  # truncated mid multi-byte character
    ],
)
def test_a_non_json_body_is_a_provider_outage(monkeypatch, body: bytes) -> None:
    _serve(monkeypatch, body)

    with pytest.raises(llm.ProviderError):
        llm._post_with_rate_limit_retry(urllib.request.Request("https://example.invalid"))


def test_the_outage_message_shows_what_came_back(monkeypatch) -> None:
    """Without a snippet of the body this failure is undiagnosable from the log."""
    _serve(monkeypatch, b"<html>Attention Required! Cloudflare</html>")

    with pytest.raises(llm.ProviderError, match="Cloudflare"):
        llm._post_with_rate_limit_retry(urllib.request.Request("https://example.invalid"))


def test_a_valid_body_still_parses(monkeypatch) -> None:
    _serve(monkeypatch, b'{"choices": [{"message": {"content": "hi"}}]}')

    body = llm._post_with_rate_limit_retry(urllib.request.Request("https://example.invalid"))

    assert body["choices"][0]["message"]["content"] == "hi"


def test_a_broken_model_listing_is_an_outage_not_a_crash(monkeypatch) -> None:
    """Model discovery runs during fallback, when the provider is already unhealthy."""
    _serve(monkeypatch, b"<html>503</html>")

    with pytest.raises(llm.ProviderError):
        llm._discover_chat_models("https://example.invalid/v1", "key")
