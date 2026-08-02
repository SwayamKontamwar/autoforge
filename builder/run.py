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
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from builder import backlog, backlog_gen, devlog
from builder.guardrail import GuardrailResult, count_tests
from builder.guardrail import run as run_guardrail
from builder.llm import Patch, ProviderError, get_provider

ALLOWED_PREFIXES = ("app/", "tests/")
CONTEXT_BUDGET = 16000
# The file listing is capped separately: it grows with every task forever, while
# file bodies are bounded by whatever fits after it.
LISTING_BUDGET = 3000
REPLENISH_THRESHOLD = 40
REPLENISH_BATCH = 80
# Re-log an ongoing outage this often. Comfortably inside GitHub's 60-day
# inactivity window, which is when it disables scheduled workflows.
HEARTBEAT_DAYS = 14


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


# Attempt counts live in the state dict keyed by task text; failures hang off this
# reserved key so both survive in one committed file.
_FAILURES_KEY = "__last_failures__"


def _remember_failure(state: dict, task: str, log: str) -> None:
    state.setdefault(_FAILURES_KEY, {})[task] = _tail(log)


def _forget_failure(state: dict, task: str) -> None:
    state.get(_FAILURES_KEY, {}).pop(task, None)


def _close_task_state(state: dict, task: str) -> None:
    """Drop everything remembered about a task that will never be attempted again.

    Both the attempt count and the stored traceback are only useful while a task is
    still live. Left behind, they accumulate one entry per finished task for the
    life of the repository — a file that grows forever in a project designed to run
    for years.
    """
    state.pop(task, None)
    _forget_failure(state, task)


def _previous_failure(state: dict, task: str) -> str:
    failures = state.get(_FAILURES_KEY)
    return failures.get(task, "") if isinstance(failures, dict) else ""


def _with_failure_note(context: str, failure: str) -> str:
    """Append the last guardrail failure so a retry is not a blind repeat.

    Without this the model receives a byte-identical prompt on every attempt and
    reliably makes the same mistake until the task is skipped — work abandoned one
    small fix away from passing. Handing back the traceback is what turns three
    wasted attempts into a correction.
    """
    return (
        f"{context}\n\n"
        "## Your previous attempt at this task failed\n\n"
        "You have already tried this task once. The patch was reverted because the "
        "guardrail failed with the output below. Read it carefully and fix the cause; "
        "do not submit the same patch again. Note that a change to one model or "
        "function often requires updating the others that use it.\n\n"
        f"```\n{failure}\n```\n"
    )


# Words that appear in nearly every backlog item and so carry no signal about
# which files a task touches.
_STOPWORDS = frozenset(
    """a an and the to for of in on with add adds added support use using make
    ensure that this it its into from when where new create creates return returns
    handle handles allow allows so is are be given then also each any all app
    tests test py module code function class method value values""".split()
)


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOPWORDS}


def _ranked_files(repo_root: Path, task_text: str) -> list[Path]:
    """Order source files by how likely they are to matter to this task.

    Alphabetical order is fine for ten files and useless for a thousand: the same
    handful of files that happen to sort first would be sent every single time,
    the task's actual subject would never be visible, and no test file would ever
    be included at all because ``app/`` sorts before ``tests/``. This repository is
    supposed to keep working after years of daily commits, so file selection has to
    stay useful as the tree grows rather than degrade into an alphabetical prefix.
    """
    tracked = sorted(
        p
        for prefix in ALLOWED_PREFIXES
        for p in (repo_root / prefix.rstrip("/")).rglob("*.py")
    )
    task_words = _words(task_text)

    def rank(path: Path) -> tuple[int, int, str]:
        rel = str(path.relative_to(repo_root))
        named = 0 if rel and rel in task_text else 1
        overlap = len(_words(rel.replace("/", " ").replace("_", " ")) & task_words)
        return (named, -overlap, rel)

    return sorted(tracked, key=rank)


def _build_context(repo_root: Path, task_text: str = "") -> str:
    ranked = _ranked_files(repo_root, task_text)

    # The listing has to be capped too. Left unbounded it outgrows the model's
    # context and the free tier's per-minute token allowance on its own — measured
    # at ~141k characters for 6k files — at which point every future run fails on
    # size alone and the repository stops building itself for good.
    shown: list[str] = []
    listing_used = 0
    for path in ranked:
        rel = str(path.relative_to(repo_root))
        if listing_used + len(rel) + 1 > LISTING_BUDGET:
            break
        shown.append(rel)
        listing_used += len(rel) + 1
    hidden = len(ranked) - len(shown)
    listing = "\n".join(shown)
    if hidden > 0:
        listing += f"\n... and {hidden} more files (most relevant to this task shown first)"
    sections = [f"Files:\n{listing}\n"]

    budget = CONTEXT_BUDGET
    for path in ranked:
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


def _autofix(repo_root: Path, patch: Patch) -> None:
    """Auto-repair safe, trivial lint issues in the generated files before judging.

    Operates only on the exact files the model wrote (already proven in-bounds), so
    nothing else in the tree is touched. Logic mistakes still fail the guardrail's
    tests; this only fixes style the model got slightly wrong (import order, unused
    imports, whitespace), turning otherwise-good work into a clean commit instead of
    a needless revert.
    """
    paths = [file.path for file in patch.files if (repo_root / file.path).exists()]
    if not paths:
        return
    for tool in (["check", "--fix", "--quiet"], ["format", "--quiet"]):
        subprocess.run(
            [sys.executable, "-m", "ruff", *tool, *paths],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )


def _revert(repo_root: Path) -> None:
    for prefix in ALLOWED_PREFIXES:
        _git(repo_root, "checkout", "--", prefix, check=False)
        _git(repo_root, "clean", "-fd", prefix, check=False)


def _push(repo_root: Path, attempts: int = 3) -> bool:
    """Push, rebasing onto the remote if it moved under us.

    The bot commits work that has already passed the guardrail, so losing it to a
    rejected push is the worst outcome available: the run fails red, the task is
    marked done locally, and the code is thrown away. A human pushing between this
    job's checkout and its push is enough to trigger it. Rebase and retry instead,
    and if the rebase genuinely conflicts, fail loudly rather than force-pushing
    over someone else's commit.
    """
    branch = _git(repo_root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    for attempt in range(attempts):
        if _git(repo_root, "push", "origin", "HEAD", check=False).returncode == 0:
            print("pushed")
            return True
        if attempt == attempts - 1:
            break
        print("push rejected; remote moved, rebasing and retrying")
        pull = _git(repo_root, "pull", "--rebase", "origin", branch, check=False)
        if pull.returncode != 0:
            _git(repo_root, "rebase", "--abort", check=False)
            print("rebase onto the remote conflicted; not force-pushing", file=sys.stderr)
            return False
    print("could not push after retrying", file=sys.stderr)
    return False


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
        _push(repo_root)


def _outage_already_logged(repo_root: Path, provider: str) -> bool:
    """True when an outage for ``provider`` is already recorded and still fresh.

    Backlog replenishment is bookkeeping, not progress, so it is skipped when looking
    back. This lets the loop log a provider outage once and then stay silent while it
    lasts, instead of appending an identical "blocked" commit on every scheduled run.

    Silence is deliberately not permanent: GitHub disables scheduled workflows after
    60 days without repository activity, so a long outage that produced no commits at
    all would quietly kill the schedule and end the experiment for good. After
    ``HEARTBEAT_DAYS`` the outage is re-logged, which keeps the repository active and
    the cron alive while still cutting three notes a day down to roughly two a month.
    """
    result = _git(repo_root, "log", "--pretty=%cI%x09%s", check=False)
    if result.returncode != 0:
        return False
    marker = f"forge: log blocked task ({provider} unavailable)"
    for line in result.stdout.splitlines():
        stamp, _, subject = line.partition("\t")
        subject = subject.strip()
        if not subject or subject.startswith("forge: replenish backlog"):
            continue
        if subject != marker:
            return False
        try:
            logged_at = datetime.fromisoformat(stamp.strip())
        except ValueError:
            return True
        age = datetime.now(timezone.utc) - logged_at
        return age < timedelta(days=HEARTBEAT_DAYS)
    return False


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

    if backlog.open_count(backlog_path) < REPLENISH_THRESHOLD:
        new_tasks = backlog_gen.replenish(repo_root, backlog_path, REPLENISH_BATCH)
        backlog.append_tasks(backlog_path, new_tasks, heading="Auto-generated follow-up work")
        devlog.append(
            devlog_path,
            "replenished",
            f"backlog running low; appended {len(new_tasks)} renewable tasks",
            "The curated backlog is nearly done, so the runtime generated more work "
            "from the toolkit it has already built. It never runs out.",
        )
        print(f"replenished backlog with {len(new_tasks)} tasks")
        _commit(repo_root, f"forge: replenish backlog (+{len(new_tasks)} tasks)", push)

    task = backlog.next_task(backlog_path)
    if task is None:
        print("backlog is empty; nothing to do")
        return 0
    print(f"next task: {task.text}")

    state = _load_state(state_path)
    attempts = int(state.get(task.text, 0))

    try:
        provider = get_provider(args.provider)
        context = _build_context(repo_root, task.text)
        prior_failure = _previous_failure(state, task.text)
        if prior_failure:
            print("retrying with the previous guardrail failure as feedback")
            context = _with_failure_note(context, prior_failure)
        patch = provider.generate(task.text, context)
    except ProviderError as exc:
        # A provider outage is infrastructure trouble, not project progress. Record it
        # once, then stay quiet until it recovers: an outage lasting months must not
        # bury the dev log under thousands of identical "blocked" commits.
        if _outage_already_logged(repo_root, args.provider):
            print(f"provider '{args.provider}' still unavailable ({exc}); already logged")
            return 0
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
        if attempts >= args.max_attempts:
            backlog.mark_done(
                backlog_path, task.index, note=f"skipped after {attempts} out-of-bounds patches"
            )
            status = "skipped"
            message = "forge: skip task after repeated out-of-bounds patches"
            detail = (
                f"Patch rejected: {reason}\n\n"
                f"Skipped after {attempts} out-of-bounds attempts so the backlog keeps moving."
            )
            _close_task_state(state, task.text)
        else:
            status = "rejected"
            message = "forge: reject out-of-bounds patch"
            detail = f"Patch rejected: {reason}"
        _save_state(state_path, state)
        devlog.append(devlog_path, status, task.text, detail)
        _commit(repo_root, message, push)
        return 0

    tests_before = count_tests(repo_root)
    _apply(repo_root, patch)
    _autofix(repo_root, patch)
    result = run_guardrail(repo_root)

    if result.ok:
        # A green suite is only meaningful if it is still the same suite. Patches may
        # write anywhere under tests/, so a task can be "completed" by replacing a
        # test file with a thinner one: ruff, import and pytest all pass, on less
        # coverage. Left unchecked that quietly dismantles the one guarantee this
        # repository makes about its own history.
        tests_after = count_tests(repo_root)
        if tests_before > 0 and 0 <= tests_after < tests_before:
            result = GuardrailResult(
                ok=False,
                log=(
                    f"{result.log}\n$ test-suite check\n"
                    f"Rejected: the suite shrank from {tests_before} to {tests_after} "
                    "collected tests. Implement the task without removing or replacing "
                    "existing tests.\n"
                ),
            )

    if result.ok:
        _close_task_state(state, task.text)
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

    # Distinguish "the model wrote bad code" from "this checkout is broken". If the
    # guardrail still fails with the patch reverted, the failure predates the model:
    # a dependency released a new lint rule, a transitive break, a broken runner.
    # Blaming the task there would burn three attempts, skip it, and then do the same
    # to every remaining task — silently shredding the backlog while every run still
    # reports success. Record it instead and change nothing.
    baseline = run_guardrail(repo_root)
    if not baseline.ok:
        print("guardrail fails on a clean tree; environment is broken, not the patch")
        if not _outage_already_logged(repo_root, "environment"):
            devlog.append(
                devlog_path,
                "blocked",
                task.text,
                "The guardrail fails on a clean checkout, before any generated code is "
                "applied, so the build environment is broken rather than the patch. The "
                "task is left untouched and no attempt was counted.\n\n"
                f"{_tail(baseline.log)}",
            )
            _commit(repo_root, "forge: log blocked task (environment unavailable)", push)
        return 0

    attempts += 1
    state[task.text] = attempts
    _remember_failure(state, task.text, result.log)

    if attempts >= args.max_attempts:
        backlog.mark_done(
            backlog_path, task.index, note=f"skipped after {attempts} failed attempts"
        )
        status, message = "skipped", "forge: skip task after repeated guardrail failures"
        _close_task_state(state, task.text)
    else:
        status, message = "failed", "forge: log failed attempt (code reverted)"

    _save_state(state_path, state)

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
