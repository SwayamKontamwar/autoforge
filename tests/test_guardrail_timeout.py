"""The guardrail must treat a hang as a failed patch, not as a crash.

Every guardrail check runs generated code, so any of them can fail to terminate:
a test that sleeps, waits on a socket, or loops forever. If the resulting timeout
escapes as an exception it kills the whole run *before* the patch is reverted and
*before* the attempt is recorded, so the same task is chosen again next time and
hangs again -- permanently, on every future run. These tests pin the behaviour
that keeps the loop moving instead.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from builder import guardrail


def _shrink_timeout(monkeypatch, seconds: int = 1) -> None:
    monkeypatch.setattr(guardrail, "CHECK_TIMEOUT_SECONDS", seconds)


def test_a_hanging_check_fails_instead_of_raising(tmp_path: Path, monkeypatch) -> None:
    _shrink_timeout(monkeypatch)

    ok, log = guardrail._run(
        "pytest",
        [sys.executable, "-c", "import time; time.sleep(30)"],
        tmp_path,
    )

    assert ok is False
    assert "timed out" in log


def test_the_timeout_log_tells_the_model_what_went_wrong(tmp_path: Path, monkeypatch) -> None:
    """The log is fed back into the next attempt, so it has to be actionable."""
    _shrink_timeout(monkeypatch)

    _, log = guardrail._run(
        "pytest", [sys.executable, "-c", "import time; time.sleep(30)"], tmp_path
    )

    assert "never finished" in log
    assert "sleep" in log


def test_a_hanging_check_stops_the_guardrail_at_that_check(tmp_path: Path, monkeypatch) -> None:
    """A timeout is a first-class failure: no later check runs, and ok is False."""
    _shrink_timeout(monkeypatch)
    calls: list[str] = []

    real_run = guardrail._run

    def _tracked(label: str, args: list[str], cwd: Path) -> tuple[bool, str]:
        calls.append(label)
        if label == "ruff check":
            return real_run(label, [sys.executable, "-c", "import time; time.sleep(30)"], cwd)
        return True, ""

    monkeypatch.setattr(guardrail, "_run", _tracked)

    result = guardrail.run(tmp_path)

    assert result.ok is False
    assert calls == ["ruff check"]


def test_a_hanging_collection_reports_unknown_not_zero(tmp_path: Path, monkeypatch) -> None:
    """-1 means "could not measure"; 0 would mean "the suite is empty".

    The caller only rejects a patch when the count actually drops, so conflating
    the two would reject every patch whenever collection happened to hang.
    """
    _shrink_timeout(monkeypatch)

    def _hang(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="pytest", timeout=1)

    monkeypatch.setattr(subprocess, "run", _hang)

    assert guardrail.count_tests(tmp_path) == -1
