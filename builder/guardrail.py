"""The correctness guardrail: lint, tests, and an import smoke check.

Generated code is committed only if every check here passes. This is the single
promise the experiment makes about its own history: it may contain imperfect
design, but it never contains a state that fails to lint, import, or test.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

# Every subprocess here runs generated code, so any of them can hang: a test that
# sleeps, waits on a socket, or loops forever. An unbounded wait would stall the
# job until the runner is killed; an *unhandled* timeout is worse still, because it
# escapes as an exception, leaves the patch applied, and records no attempt — so the
# same task is retried and hangs again on every future run, permanently.
CHECK_TIMEOUT_SECONDS = 600

# Enough to hold any honest pytest failure report, far short of what it takes to
# exhaust a runner. Only the tail is kept, since that is where failures are.
OUTPUT_LIMIT_BYTES = 8 * 1024 * 1024
_TAIL_BYTES = 256 * 1024
_POLL_SECONDS = 0.05
_GRACE_SECONDS = 5


@dataclass
class GuardrailResult:
    """Outcome of running the guardrail."""

    ok: bool
    log: str


def _drain(label: str, args: list[str], cwd: Path) -> tuple[int | None, str, bool]:
    """Run a command, capped in both time and output size.

    ``capture_output=True`` buffers everything the child writes, in memory, with no
    limit. A generated test that prints inside a loop reaches gigabytes long before
    the timeout: measured, 400 MB of child output cost 1.8 GB of resident memory, so
    a runner's 16 GB is gone in minutes. The orchestrator is then killed by the OOM
    reaper -- not caught, *killed* -- before it can revert or record the attempt, and
    since the attempt count is committed, the next run picks the same task and does it
    again. Forever. Output therefore goes to a spill file that is polled for size, and
    a flood is stopped the same way a hang is.
    """
    with tempfile.TemporaryFile() as sink:
        try:
            proc = subprocess.Popen(args, cwd=cwd, stdout=sink, stderr=subprocess.STDOUT)
        except OSError as exc:
            return None, f"could not start the command: {exc}", False
        deadline = time.monotonic() + CHECK_TIMEOUT_SECONDS
        flooded = False
        while proc.poll() is None:
            if os.fstat(sink.fileno()).st_size > OUTPUT_LIMIT_BYTES:
                flooded = True
                break
            if time.monotonic() > deadline:
                break
            time.sleep(_POLL_SECONDS)
        code = proc.poll()
        if code is None:
            proc.terminate()
            try:
                proc.wait(timeout=_GRACE_SECONDS)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        size = os.fstat(sink.fileno()).st_size
        sink.seek(max(0, size - _TAIL_BYTES))
        text = sink.read().decode("utf-8", "replace").strip()
        if size > _TAIL_BYTES:
            text = f"... ({size} bytes of output, showing the last {_TAIL_BYTES})\n{text}"
        return code, text, flooded


def _run(label: str, args: list[str], cwd: Path) -> tuple[bool, str]:
    code, output, flooded = _drain(label, args, cwd)
    if flooded:
        return False, (
            f"$ {label}\n(stopped after writing more than {OUTPUT_LIMIT_BYTES} bytes)\n"
            "The command flooded its output. Generated code must not print inside an "
            "unbounded loop.\n"
            f"{output}\n"
        )
    if code is None:
        # A hang is a failed patch like any other: revert it, count the attempt, and
        # tell the model what happened. Letting the exception escape instead would
        # wedge the loop on this task forever.
        return False, (
            f"$ {label}\n(timed out after {CHECK_TIMEOUT_SECONDS}s)\n"
            "The command never finished. Generated code must not sleep, wait on "
            "network or user input, or loop without a termination condition.\n"
            f"{output}\n"
        )
    return code == 0, f"$ {label}\n(exit {code})\n{output}\n"


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
    # Collection alone can hang, or flood, on import-time side effects. Either way the
    # answer is unknown, not zero: the caller treats -1 as "no comparison possible"
    # rather than "the suite is empty", which would read as a catastrophic shrink.
    code, output, flooded = _drain(
        "pytest --collect-only",
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        repo_root,
    )
    if flooded or code != 0:
        return -1
    return parse_collected(output)


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
