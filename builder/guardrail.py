"""The correctness guardrail: lint, tests, and an import smoke check.

Generated code is committed only if every check here passes. This is the single
promise the experiment makes about its own history: it may contain imperfect
design, but it never contains a state that fails to lint, import, or test.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# Every subprocess here runs generated code, so any of them can hang: a test that
# sleeps, waits on a socket, or loops forever. An unbounded wait would stall the
# job until the runner is killed; an *unhandled* timeout is worse still, because it
# escapes as an exception, leaves the patch applied, and records no attempt — so the
# same task is retried and hangs again on every future run, permanently.
CHECK_TIMEOUT_SECONDS = 600


@dataclass
class GuardrailResult:
    """Outcome of running the guardrail."""

    ok: bool
    log: str


def _run(label: str, args: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=CHECK_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        # A hang is a failed patch like any other: revert it, count the attempt, and
        # tell the model what happened. Letting the exception escape instead would
        # wedge the loop on this task forever.
        return False, (
            f"$ {label}\n(timed out after {CHECK_TIMEOUT_SECONDS}s)\n"
            "The command never finished. Generated code must not sleep, wait on "
            "network or user input, or loop without a termination condition.\n"
        )
    ok = proc.returncode == 0
    output = (proc.stdout + proc.stderr).strip()
    return ok, f"$ {label}\n(exit {proc.returncode})\n{output}\n"


def parse_collected(output: str) -> int:
    """Count collected tests from ``pytest --collect-only -q`` output.

    Deliberately tolerant: pytest has printed this three different ways across
    recent majors — a "N tests collected" summary, one "path: N" line per file,
    and one node id per line. A parser that knows only the current format would
    silently start returning "no tests" after a routine pytest upgrade, which here
    means silently dropping a safety check rather than failing loudly.
    """
    summary = re.search(r"(\d+)\s+tests?\s+collected", output)
    if summary:
        return int(summary.group(1))
    per_file = re.findall(r"^\S+:\s+(\d+)$", output, re.MULTILINE)
    if per_file:
        return sum(int(n) for n in per_file)
    node_ids = [ln for ln in output.splitlines() if "::" in ln]
    return len(node_ids)


def count_tests(repo_root: Path) -> int:
    """Return how many tests pytest can collect, or -1 if collection failed.

    Generated patches may write anywhere under ``tests/``, so a model implementing
    a task can overwrite an existing test file with a thinner one. Lint, import and
    pytest would all still pass — on a smaller suite. Over a long run that erodes
    the safety net every other guarantee here depends on, while each run keeps
    reporting success.
    """
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=CHECK_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        # Collection alone can hang on import-time side effects. Unknown, not zero:
        # the caller treats -1 as "no comparison possible" rather than "no tests".
        return -1
    if proc.returncode != 0:
        return -1
    return parse_collected(proc.stdout)


def run(repo_root: Path) -> GuardrailResult:
    """Run ruff, an import check, and pytest. Stop at the first failure."""
    checks: list[tuple[str, list[str]]] = [
        ("ruff check", [sys.executable, "-m", "ruff", "check", "."]),
        ("import app.main", [sys.executable, "-c", "import app.main"]),
        ("pytest", [sys.executable, "-m", "pytest"]),
    ]
    log = ""
    for label, args in checks:
        ok, section = _run(label, args, repo_root)
        log += section
        if not ok:
            return GuardrailResult(ok=False, log=log)
    return GuardrailResult(ok=True, log=log)
