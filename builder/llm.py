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


# Groq's free tier meters prompt *and* completion against one tokens-per-minute
# allowance, and rejects the whole request when the sum is over it -- not when it is
# used up, when it is *asked for*. So a fixed completion budget is wrong twice over:
# too big and every request is refused outright (observed live: "Limit 8000,
# Requested 20976" as an HTTP 413), too small and every answer is cut off. It has to
# be whatever is left after the prompt.
_TOKEN_BUDGET = int(os.getenv("TOKEN_BUDGET", "8000"))
_MIN_COMPLETION_TOKENS = 1200
_TOKENS_PER_CHAR = 0.28
_BUDGET_MARGIN_TOKENS = 250


def _completion_budget(*prompts: str) -> int:
    """How many tokens are left for the answer once the prompt is paid for.

    The free tier meters the question and the requested answer against a single
    allowance and rejects the request outright if the pair exceeds it -- it charges
    for the answer that was *asked for*, not the one that came back. A fixed
    ``max_tokens`` therefore stops working the moment the prompt grows, which is
    exactly what happened in production: HTTP 413, "Limit 8000, Requested 20976",
    on every single run, with a perfectly good key.
    """
    spent = int(sum(len(part) for part in prompts) * _TOKENS_PER_CHAR)
    room = _TOKEN_BUDGET - spent - _BUDGET_MARGIN_TOKENS
    if room < _MIN_COMPLETION_TOKENS:
        # Asking anyway earns an opaque 413 that looks like an outage, so the run
        # would wait for a recovery that cannot come: the prompt is derived from the
        # repository and the task, so it will be just as large next time. Fail the
        # task instead, so it is retried a few times and then skipped.
        raise PromptTooLarge(
            f"the question needs about {spent} tokens and the allowance is "
            f"{_TOKEN_BUDGET}, leaving no room for an answer; lower CONTEXT_BUDGET "
            f"or raise TOKEN_BUDGET"
        )
    return room


class ProviderError(RuntimeError):
    """Raised when a provider cannot produce a usable patch."""


class DoesNotFit(RuntimeError):
    """Raised when a request cannot fit the token allowance, in either direction.

    Deliberately not a :class:`ProviderError`. An outage is retried forever without
    counting an attempt, which is right for a service that will come back -- but a
    request that does not fit is a property of this repository and this task, so it
    will not fit next time either. Counting it means the task is retried a few times
    and then skipped, and the loop keeps moving.
    """


class PromptTooLarge(DoesNotFit):
    """Raised when the question alone would exhaust the allowance."""


class TruncatedResponse(DoesNotFit):
    """Raised when the provider stopped mid-answer at its completion limit.

    Deliberately not a :class:`ProviderError`. An outage is retried forever without
    counting an attempt, which is right for a provider that is down and wrong here:
    a task whose answer does not fit will never fit, so treating it as an outage
    would stall the loop silently. It is a failed attempt with actionable feedback
    instead, and the task is skipped after the usual three.
    """


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
            summary = stripped[len("SUMMARY:") :].strip()
        elif stripped.startswith(_FILE_MARKER):
            flush()
            header = stripped[len(_FILE_MARKER) :].strip()
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
    if not isinstance(data, dict):
        # A bare array of file objects is a shape models emit for this prompt often
        # enough to matter. Reaching .get() on it raises AttributeError, which is not
        # a ProviderError, so it escapes the run instead of being retried.
        raise ProviderError("model returned JSON that is not an object")
    files_raw = data.get("files")
    if not isinstance(files_raw, list) or not files_raw:
        raise ProviderError("patch contained no files")
    files: list[File] = []
    for item in files_raw:
        if not isinstance(item, dict):
            raise ProviderError("each file needs a string path and content")
        path = item.get("path")
        content = item.get("content")
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
            '__version__ = "0.1.0"\n\n\n'
            "def get_version() -> str:\n"
            '    """Return the current autoforge app version string."""\n'
            "    return __version__\n"
        )
        version_test = (
            "from app.version import get_version\n\n\n"
            "def test_get_version_is_semver_like():\n"
            '    parts = get_version().split(".")\n'
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


def _decode_json_body(raw: bytes, source: str) -> dict:
    """Parse a provider response body, or fail as a provider outage.

    A 200 does not guarantee JSON. Proxies, gateways and bot-protection layers all
    serve HTML interstitials with a success status, and a body can be truncated
    mid-character. Letting the decode error escape turns a provider-side hiccup into
    a crashed run; as a ProviderError it takes the outage path instead, which logs
    it and retries on the next schedule.
    """
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        snippet = raw.decode("utf-8", "replace")[:200].strip()
        raise ProviderError(f"{source} returned a non-JSON body: {snippet}") from exc


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
                return _decode_json_body(response.read(), "provider")
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
        except TimeoutError as exc:
            # urllib raises this straight through rather than wrapping it in a
            # URLError, so it used to escape main() -- after the task was chosen and
            # before the attempt was recorded, which wedges the loop on that task.
            # A provider that stops answering is an outage like any other.
            if attempt < _RATE_LIMIT_ATTEMPTS - 1:
                print(f"provider timed out; waiting {delay:.0f}s and retrying")
                time.sleep(delay)
                delay = min(delay * 2, _MAX_BACKOFF_SECONDS)
                continue
            raise ProviderError(f"provider timed out: {exc}") from exc
        except OSError as exc:
            raise ProviderError(f"provider connection failed: {exc}") from exc
    raise ProviderError("provider rate limit did not clear")


_MODEL_UNAVAILABLE_HINTS = (
    "model_not_found",
    "model not found",
    "does not exist",
    "decommissioned",
    "deprecated",
    "no longer supported",
    "has been retired",
)

# Providers list far more than chat models on the same endpoint. Anything matching
# these is the wrong tool for writing code and must never be picked as a fallback.
_NON_CHAT_HINTS = ("whisper", "tts", "embed", "guard", "moderation", "rerank", "-asr")

_MAX_FALLBACK_MODELS = 3


def _looks_model_unavailable(message: str) -> bool:
    lowered = message.lower()
    return any(hint in lowered for hint in _MODEL_UNAVAILABLE_HINTS)


def _discover_chat_models(base_url: str, api_key: str) -> list[str]:
    """Ask the provider which models it currently serves, newest listing order kept."""
    request = urllib.request.Request(
        base_url.rstrip("/") + "/models",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": _USER_AGENT,
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = _decode_json_body(response.read(), "model listing")
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return []
    ids = [str(entry.get("id", "")) for entry in body.get("data", []) if isinstance(entry, dict)]
    return [
        model_id
        for model_id in ids
        if model_id and not any(hint in model_id.lower() for hint in _NON_CHAT_HINTS)
    ]


# Substrings that mark a model as the small/fast variant of its family. They are
# usable, but they are the last thing to fall back to for writing code.
_LIGHTWEIGHT_HINTS = ("mini", "nano", "small", "instant", "-8b", "-1b", "-3b", "lite")


def _rank_fallbacks(candidates: list[str], configured: str) -> list[str]:
    """Order replacements by how likely they are to match the configured model.

    ``/models`` answers in arbitrary order, so an unranked fallback is a coin flip
    between a peer of the retired model and the smallest model on the menu. Same
    vendor first, lightweight variants last, alphabetical within a tier so the
    choice is reproducible when someone is trying to explain a run months later.
    """
    vendor = configured.split("/")[0].lower() if "/" in configured else ""

    def key(model_id: str) -> tuple[int, int, str]:
        lowered = model_id.lower()
        same_vendor = 0 if vendor and lowered.startswith(f"{vendor}/") else 1
        lightweight = 1 if any(h in lowered for h in _LIGHTWEIGHT_HINTS) else 0
        return (lightweight, same_vendor, lowered)

    return sorted(candidates, key=key)


def _chat_completion(
    base_url: str, path: str, model: str, api_key: str, task: str, context: str
) -> str:
    """Run one completion, surviving the retirement of the configured model.

    Hosted models are withdrawn on a timescale far shorter than this repository is
    meant to run — the original default was decommissioned during development. A
    retired model answers every future run with the same 4xx, so without this the
    project stops building itself permanently and says only "provider error" while
    doing it. Falling back to whatever the provider actually serves keeps the loop
    alive; a bad substitute can still only produce a patch the guardrail rejects.
    """
    try:
        return _single_completion(base_url, path, model, api_key, task, context)
    except ProviderError as exc:
        if not _looks_model_unavailable(str(exc)):
            raise
        print(f"configured model {model!r} is unavailable: {exc}")
        candidates = _rank_fallbacks(
            [m for m in _discover_chat_models(base_url, api_key) if m != model], model
        )
        for candidate in candidates[:_MAX_FALLBACK_MODELS]:
            print(f"MODEL FALLBACK: retrying with {candidate!r}")
            try:
                return _single_completion(base_url, path, candidate, api_key, task, context)
            except ProviderError as inner:
                if _looks_model_unavailable(str(inner)):
                    continue
                raise
        raise ProviderError(
            f"configured model {model!r} is unavailable and no served replacement "
            f"worked (tried {candidates[:_MAX_FALLBACK_MODELS]}): {exc}"
        ) from exc


def _single_completion(
    base_url: str, path: str, model: str, api_key: str, task: str, context: str
) -> str:
    user_prompt = _user_prompt(task, context)
    payload = json.dumps(
        {
            "model": model,
            "temperature": 0.2,
            # Without an explicit budget the provider picks its own, and a file
            # rewrite that runs past it comes back cut off mid-line. Observed live:
            # a patch whose last string literal was never closed, reported as the
            # model writing bad code. As the files it must rewrite grow over the
            # years, that gets more likely, not less.
            "max_tokens": _completion_budget(_SYSTEM_PROMPT, user_prompt),
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
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
    return _extract_completion(_post_with_rate_limit_retry(request))


def _extract_completion(body: object) -> str:
    """Pull the assistant's text out of a chat completion, or say why we cannot."""
    try:
        choice = body["choices"][0]  # type: ignore[index]
        content = choice["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError(f"unexpected provider response shape: {body}") from exc
    if isinstance(choice, dict) and choice.get("finish_reason") == "length":
        # The answer is not wrong, it is unfinished. Observed live: a rewrite of a
        # growing test file came back with its last string literal never closed, and
        # was reported as the model writing bad syntax. Saying what actually happened
        # turns that into feedback the model can act on, and stops a good task being
        # skipped after three cut-off attempts.
        raise TruncatedResponse(
            "the provider stopped mid-answer at the completion limit. Return fewer "
            "files, and keep each file small; split large work across runs."
        )
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
