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
import urllib.error
import urllib.request
from dataclasses import dataclass


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


_SYSTEM_PROMPT = (
    "You are autoforge, an autonomous contributor to a small FastAPI URL-shortener "
    "written in Python. You implement exactly one backlog item per turn.\n\n"
    "Hard rules:\n"
    "- Only create or modify files under app/ and tests/.\n"
    "- Add or update a pytest test that proves the feature you built.\n"
    "- Keep the code lint-clean for ruff (rules E, F, I; line length 100).\n"
    "- Preserve existing endpoints and their behaviour unless the task says otherwise.\n"
    "- Return whole-file contents for every file you touch, not diffs.\n\n"
    "Respond with ONLY a JSON object, no prose and no markdown fences, shaped like:\n"
    '{"summary": "<= 72 char imperative summary", '
    '"files": [{"path": "app/...", "content": "<full file text>"}]}'
)


def _user_prompt(task: str, context: str) -> str:
    return (
        f"Backlog item to implement:\n{task}\n\n"
        f"Current repository contents:\n{context}\n\n"
        "Return the JSON patch now."
    )


def parse_patch(raw: str) -> Patch:
    """Parse a model response into a :class:`Patch`, tolerating code fences."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:] if lines else lines
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        data = json.loads(text)
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
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        raise ProviderError(f"provider HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ProviderError(f"provider unreachable: {exc.reason}") from exc
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError(f"unexpected provider response shape: {body}") from exc


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
