"""Language-model providers that turn a backlog item into a code patch.

Every provider returns the same strict contract — a :class:`Patch` of whole-file
rewrites plus a one-line summary — so the orchestrator never cares which model
wrote the code. This keeps the experiment free and portable: if GitHub Models is
unavailable, drop in any OpenAI-compatible free tier (Groq, Gemini, OpenRouter,
a local Ollama) by setting a few environment variables.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

_USER_AGENT = "autoforge/1.0 (+https://github.com/SwayamKontamwar/autoforge)"

# A free-tier key is metered per minute, so a rate limit is a short wait rather
# than an outage. Kept small enough that a stuck provider still ends the job.
_RATE_LIMIT_ATTEMPTS = 3
_MAX_BACKOFF_SECONDS = 75.0


class ProviderError(RuntimeError):
    """Raised when a provider cannot produce a usable patch."""


@dataclass
class File:
    path: str
    content: str


@dataclass
class Patch:
    files: list[File]
    summary: str


_FILE_MARKER = "=== FILE:"
_END_MARKER = "=== END ==="

_SYSTEM_PROMPT = (
    "You are autoforge, an autonomous contributor to a small Python project (a FastAPI "
    "service plus a standard-library-style utility toolkit). You implement exactly one "
    "backlog item per turn.\n\n"
    "Hard rules:\n"
    "- Only create or modify files under app/ and tests/.\n"
    "- Add or update a pytest test that proves the feature you built.\n"
    "- Keep the code lint-clean for ruff (rules E, F, I; line length 100).\n"
    "- Preserve existing behaviour unless the task says otherwise.\n"
    "- Output the WHOLE contents of every file you touch, not diffs.\n\n"
    "Respond in EXACTLY this plain-text format, and nothing else — no prose, no "
    "markdown fences, no JSON:\n\n"
    "SUMMARY: <<=72 character imperative summary>\n"
    f"{_FILE_MARKER} app/relative/path.py ===\n"
    "<the complete raw file content, written verbatim>\n"
    f"{_FILE_MARKER} tests/relative/path.py ===\n"
    "<the complete raw file content, written verbatim>\n"
    f"{_END_MARKER}\n\n"
    "Write file contents exactly as they should appear on disk. Do NOT escape quotes, "
    "backslashes, or newlines — just write the real characters."
)


def _user_prompt(task: str, context: str) -> str:
    return (
        f"Backlog item to implement:\n{task}\n\n"
        f"Current repository contents:\n{context}\n\n"
        "Return the patch now, in the SUMMARY / === FILE: === / === END === format."
    )


_VALID_ESCAPES = set('"\\/bfnrtu')


def _repair_json(text: str) -> str:
    """Repair the two mistakes small models make most when emitting JSON payloads.

    1. Unescaped backslashes inside string values — code full of regex (``\\s``,
       ``\\d``) or escape sequences produces JSON that ``json.loads`` rejects with
       "Invalid \\escape". Any backslash that does not begin a valid JSON escape is
       doubled.
    2. Literal newlines/carriage returns/tabs inside string values — models often
       paste real file contents with real line breaks, which are illegal control
       characters inside a JSON string. These are converted to ``\\n``/``\\r``/``\\t``.

    Only characters *inside* string literals are touched, so structural JSON is left
    intact. This never makes correctness claims: repaired code still faces the full
    guardrail.
    """
    out: list[str] = []
    in_string = False
    i = 0
    n = len(text)
    while i < n:
        char = text[i]
        if not in_string:
            out.append(char)
            if char == '"':
                in_string = True
            i += 1
            continue
        if char == "\\":
            nxt = text[i + 1] if i + 1 < n else ""
            if nxt in _VALID_ESCAPES:
                out.append(char)
                out.append(nxt)
                i += 2
            else:
                out.append("\\\\")
                i += 1
            continue
        if char == '"':
            in_string = False
            out.append(char)
        elif char == "\n":
            out.append("\\n")
        elif char == "\r":
            out.append("\\r")
        elif char == "\t":
            out.append("\\t")
        else:
            out.append(char)
        i += 1
    return "".join(out)


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:] if lines else lines
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return text


def _parse_markers(text: str) -> Patch:
    """Parse the escaping-free ``=== FILE: path ===`` format.

    Raw file contents sit verbatim between markers, so the model never has to escape
    quotes, backslashes, or newlines — the single biggest source of unusable output
    from smaller models. This makes the loop productive on free, local models.
    """
    files: list[File] = []
    summary = ""
    current_path: str | None = None
    current: list[str] = []

    def flush() -> None:
        if current_path is not None:
            content = "\n".join(current).strip("\n")
            files.append(File(path=current_path.strip(), content=content))

    for line in text.splitlines():
        stripped = line.strip()
        if current_path is None and stripped.upper().startswith("SUMMARY:"):
            summary = stripped[len("SUMMARY:"):].strip()
        elif stripped.startswith(_FILE_MARKER):
            flush()
            header = stripped[len(_FILE_MARKER):].strip()
            if header.endswith("==="):
                header = header[:-3].strip()
            current_path = header
            current = []
        elif stripped == _END_MARKER:
            flush()
            current_path = None
            current = []
            break
        elif current_path is not None:
            current.append(line)
    else:
        flush()

    if not files:
        raise ProviderError("no files found in marker response")
    return Patch(files=files, summary=summary or "implement backlog item")


def _parse_json(text: str) -> Patch:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        try:
            data = json.loads(_repair_json(text))
        except json.JSONDecodeError as exc:
            raise ProviderError(f"model did not return valid JSON: {exc}") from exc
    files_raw = data.get("files")
    if not isinstance(files_raw, list) or not files_raw:
        raise ProviderError("patch contained no files")
    files: list[File] = []
    for item in files_raw:
        path = (item or {}).get("path")
        content = (item or {}).get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            raise ProviderError("each file needs a string path and content")
        files.append(File(path=path.strip(), content=content))
    summary = str(data.get("summary") or "").strip() or "implement backlog item"
    return Patch(files=files, summary=summary)


def parse_patch(raw: str) -> Patch:
    """Parse a model response into a :class:`Patch`.

    Prefers the escaping-free ``=== FILE: ===`` marker format (robust for small
    models); falls back to a tolerant JSON parse for models that answer in JSON.
    """
    text = _strip_fences(raw)
    if _FILE_MARKER in text:
        return _parse_markers(text)
    return _parse_json(text)


class MockProvider:
    """Offline provider used to prove the loop without a network or API key.

    Set ``FORGE_MOCK_BREAK=1`` to emit a deliberately failing patch, which is how
    the guardrail's revert path is exercised in tests and local verification.
    """

    name = "mock"

    def generate(self, task: str, context: str) -> Patch:
        if os.getenv("FORGE_MOCK_BREAK") == "1":
            return Patch(
                files=[File("tests/test_broken.py", "def test_broken():\n    assert 1 == 2\n")],
                summary="deliberately failing patch (guardrail should revert)",
            )
        version_module = (
            '"""Expose the running application version."""\n\n'
            "from __future__ import annotations\n\n"
            "__version__ = \"0.1.0\"\n\n\n"
            "def get_version() -> str:\n"
            '    """Return the current autoforge app version string."""\n'
            "    return __version__\n"
        )
        version_test = (
            "from app.version import get_version\n\n\n"
            "def test_get_version_is_semver_like():\n"
            "    parts = get_version().split(\".\")\n"
            "    assert len(parts) == 3\n"
            "    assert all(part.isdigit() for part in parts)\n"
        )
        return Patch(
            files=[
                File("app/version.py", version_module),
                File("tests/test_version.py", version_test),
            ],
            summary="add app version helper",
        )


def _retry_after_seconds(headers, default: float) -> float:
    """Read a provider's requested wait, clamped to something a CI run can afford."""
    for key in ("retry-after", "x-ratelimit-reset-tokens", "x-ratelimit-reset-requests"):
        raw = headers.get(key) if headers else None
        if not raw:
            continue
        text = str(raw).strip().rstrip("s")
        try:
            wait = float(text)
        except ValueError:
            continue
        return max(1.0, min(wait + 1.0, _MAX_BACKOFF_SECONDS))
    return default


def _post_with_rate_limit_retry(request) -> dict:
    """POST, waiting out rate limits instead of treating them as an outage.

    A free-tier key is measured per minute, and one code-generation call can use
    most of that budget once the model's reasoning tokens are counted. Treating the
    resulting 429 as a provider outage would skip the run entirely and leave the
    task untouched until the next schedule. Waiting a few seconds costs nothing in
    a job that runs three times a day.
    """
    delay = 5.0
    for attempt in range(_RATE_LIMIT_ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:500]
            retryable = exc.code == 429 or 500 <= exc.code < 600
            if retryable and attempt < _RATE_LIMIT_ATTEMPTS - 1:
                wait = _retry_after_seconds(exc.headers, delay)
                print(f"provider HTTP {exc.code}; waiting {wait:.0f}s and retrying")
                time.sleep(wait)
                delay = min(delay * 2, _MAX_BACKOFF_SECONDS)
                continue
            raise ProviderError(f"provider HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"provider unreachable: {exc.reason}") from exc
    raise ProviderError("provider rate limit did not clear")


def _chat_completion(
    base_url: str, path: str, model: str, api_key: str, task: str, context: str
) -> str:
    payload = json.dumps(
        {
            "model": model,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _user_prompt(task, context)},
            ],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        base_url.rstrip("/") + path,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            # urllib's default User-Agent is "Python-urllib/x.y", which sits on the
            # bot blocklist of at least one major provider's CDN: Groq answers it
            # with a Cloudflare 1010 "browser signature banned" 403 while the very
            # same request from curl succeeds. Identifying honestly costs nothing
            # and turns a permanent, silent provider outage into a working run.
            "User-Agent": _USER_AGENT,
        },
        method="POST",
    )
    body = _post_with_rate_limit_retry(request)
    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError(f"unexpected provider response shape: {body}") from exc
    if not content or not content.strip():
        # Reasoning models spend part of the completion budget thinking, and can
        # return an empty message when that budget runs out. Say so plainly rather
        # than failing later with an unhelpful "no files found" parse error.
        raise ProviderError("provider returned an empty message")
    return content


class GitHubModelsProvider:
    """Free inference through GitHub Models using the workflow ``GITHUB_TOKEN``."""

    name = "github"

    def __init__(self) -> None:
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.base_url = os.getenv("GITHUB_MODELS_URL", "https://models.github.ai/inference")
        self.model = os.getenv("MODEL_ID", "openai/gpt-4o-mini")

    def generate(self, task: str, context: str) -> Patch:
        if not self.token:
            raise ProviderError("GITHUB_TOKEN is not set")
        raw = _chat_completion(
            self.base_url, "/chat/completions", self.model, self.token, task, context
        )
        return parse_patch(raw)


class OpenAICompatProvider:
    """Any OpenAI-compatible endpoint (Groq, Gemini compat, OpenRouter, Ollama)."""

    name = "openai"

    def __init__(self) -> None:
        self.token = os.getenv("LLM_API_KEY", "")
        self.base_url = os.getenv("LLM_BASE_URL", "")
        self.model = os.getenv("MODEL_ID", "")

    def generate(self, task: str, context: str) -> Patch:
        if not self.base_url or not self.model:
            raise ProviderError("LLM_BASE_URL and MODEL_ID must be set for the openai provider")
        raw = _chat_completion(
            self.base_url, "/chat/completions", self.model, self.token, task, context
        )
        return parse_patch(raw)


def get_provider(name: str):
    """Return a provider instance for ``name`` (github, openai, or mock)."""
    providers = {
        "github": GitHubModelsProvider,
        "openai": OpenAICompatProvider,
        "mock": MockProvider,
    }
    try:
        return providers[name]()
    except KeyError:
        raise ProviderError(f"unknown provider: {name}") from None
