"""The autoforge orchestrator.

One invocation implements at most one backlog item:

1. pick the next open backlog task;
2. ask the configured model for a whole-file patch touching only app/ and tests/;
3. apply it and run the guardrail (ruff + import + pytest);
4. on success: mark the task done, log it, commit, and push;
   on failure: revert the code, log the failure, and still commit the log so the
   daily cadence and audit trail continue without ever shipping broken code.

Run ``python -m builder.run --provider mock --no-push`` to exercise it offline.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from builder import backlog, devlog
from builder.guardrail import run as run_guardrail
from builder.llm import Patch, ProviderError, get_provider

ALLOWED_PREFIXES = ("app/", "tests/")
CONTEXT_BUDGET = 16000


def _git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=check,
    )


def _is_clean(repo_root: Path) -> bool:
    return _git(repo_root, "status", "--porcelain").stdout.strip() == ""


def _load_state(state_path: Path) -> dict:
    if state_path.exists():
        try:
            return json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_context(repo_root: Path) -> str:
    sections: list[str] = []
    budget = CONTEXT_BUDGET
    tracked = sorted(
        p
        for prefix in ALLOWED_PREFIXES
        for p in (repo_root / prefix.rstrip("/")).rglob("*.py")
    )
    listing = "\n".join(str(p.relative_to(repo_root)) for p in tracked)
    sections.append(f"Files:\n{listing}\n")
    for path in tracked:
        rel = path.relative_to(repo_root)
        content = path.read_text(encoding="utf-8")
        block = f"\n--- {rel} ---\n{content}"
        if len(block) > budget:
            block = block[:budget] + "\n... (truncated)"
        budget -= len(block)
        sections.append(block)
        if budget <= 0:
            break
    return "\n".join(sections)


def _reject_reason(patch: Patch) -> str | None:
    for file in patch.files:
        norm = os.path.normpath(file.path).replace(os.sep, "/")
        if norm.startswith("/") or norm.startswith(".."):
            return f"path escapes the repository: {file.path}"
        if not norm.startswith(ALLOWED_PREFIXES):
            return f"path outside app/ or tests/: {file.path}"
    return None


def _apply(repo_root: Path, patch: Patch) -> None:
    for file in patch.files:
        target = repo_root / file.path
        target.parent.mkdir(parents=True, exist_ok=True)
        content = file.content if file.content.endswith("\n") else file.content + "\n"
        target.write_text(content, encoding="utf-8")


def _revert(repo_root: Path) -> None:
    for prefix in ALLOWED_PREFIXES:
        _git(repo_root, "checkout", "--", prefix, check=False)
        _git(repo_root, "clean", "-fd", prefix, check=False)


def _commit(repo_root: Path, message: str, push: bool) -> None:
    _git(repo_root, "add", "-A")
    if _git(repo_root, "diff", "--cached", "--quiet", check=False).returncode == 0:
        print("nothing to commit")
        return
    _git(
        repo_root,
        "-c",
        "user.name=autoforge-bot",
        "-c",
        "user.email=autoforge-bot@users.noreply.github.com",
        "commit",
        "-m",
        message,
    )
    print(f"committed: {message}")
    if push:
        _git(repo_root, "push", "origin", "HEAD")
        print("pushed")


def _tail(log: str, limit: int = 2000) -> str:
    return log if len(log) <= limit else "... (truncated)\n" + log[-limit:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the next backlog item.")
    parser.add_argument("--provider", default=os.getenv("LLM_PROVIDER", "github"))
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--backlog", default="BACKLOG.md")
    parser.add_argument("--devlog", default="DEVLOG.md")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--no-push", action="store_true")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    backlog_path = repo_root / args.backlog
    devlog_path = repo_root / args.devlog
    state_path = repo_root / ".forge" / "state.json"
    push = not args.no_push

    if not _is_clean(repo_root):
        print("working tree is not clean; aborting", file=sys.stderr)
        return 1

    task = backlog.next_task(backlog_path)
    if task is None:
        print("backlog is empty; nothing to do")
        return 0
    print(f"next task: {task.text}")

    state = _load_state(state_path)
    attempts = int(state.get(task.text, 0))

    try:
        provider = get_provider(args.provider)
        patch = provider.generate(task.text, _build_context(repo_root))
    except ProviderError as exc:
        devlog.append(
            devlog_path,
            "blocked",
            task.text,
            f"Model provider '{args.provider}' was unavailable: {exc}. "
            "No code changed; will retry next run.",
        )
        _commit(repo_root, f"forge: log blocked task ({args.provider} unavailable)", push)
        return 0

    reason = _reject_reason(patch)
    if reason is not None:
        attempts += 1
        state[task.text] = attempts
        _save_state(state_path, state)
        devlog.append(devlog_path, "rejected", task.text, f"Patch rejected: {reason}")
        _commit(repo_root, "forge: reject out-of-bounds patch", push)
        return 0

    _apply(repo_root, patch)
    result = run_guardrail(repo_root)

    if result.ok:
        state.pop(task.text, None)
        _save_state(state_path, state)
        backlog.mark_done(backlog_path, task.index)
        devlog.append(
            devlog_path,
            "success",
            task.text,
            f"{patch.summary}\n\nGuardrail: ruff + import + pytest passed.",
        )
        _commit(repo_root, f"forge: {patch.summary}", push)
        return 0

    _revert(repo_root)
    attempts += 1
    state[task.text] = attempts
    _save_state(state_path, state)

    if attempts >= args.max_attempts:
        backlog.mark_done(
            backlog_path, task.index, note=f"skipped after {attempts} failed attempts"
        )
        status, message = "skipped", "forge: skip task after repeated guardrail failures"
    else:
        status, message = "failed", "forge: log failed attempt (code reverted)"

    devlog.append(
        devlog_path,
        status,
        task.text,
        f"Guardrail failed on attempt {attempts}; code reverted.\n\n```\n{_tail(result.log)}\n```",
    )
    _commit(repo_root, message, push)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
