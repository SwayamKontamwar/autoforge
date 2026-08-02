"""Regressions for four ways the loop could stall or die without saying so.

Three of them end the run with an exception in the one window this project cannot
absorb -- after the task is chosen, before the attempt is recorded -- which leaves
the committed attempt count unchanged, so the same task is chosen and fails the same
way on every future run. The fourth is quieter and worse: it keeps every workflow
green while nothing is built at all.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from builder import guardrail, llm, run
from builder.llm import Patch, ProviderError, TruncatedResponse

from .test_run import _init_repo


class _Raises:
    """A provider that fails in a way nothing in the code path lists by name."""

    name = "raiser"

    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def generate(self, task: str, context: str) -> Patch:
        raise self._exc


@pytest.mark.parametrize(
    "exc",
    [
        TimeoutError("timed out"),
        MemoryError(),
        RecursionError("deep"),
        AttributeError("nope"),
        OSError(104, "Connection reset by peer"),
        ValueError("weird"),
    ],
    ids=lambda e: type(e).__name__,
)
def test_no_provider_failure_escapes_the_run(tmp_path: Path, monkeypatch, exc) -> None:
    """A socket timeout is the real one: urllib raises it bare, not as a URLError."""
    root = _init_repo(tmp_path, ["alpha"])
    monkeypatch.setattr(run, "get_provider", lambda name: _Raises(exc))

    assert run.main(["--repo-root", str(root), "--provider", "raiser", "--no-push"]) in (0, 1)

    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True
    ).stdout
    assert dirty.strip() == ""


def test_a_short_outage_stays_green(tmp_path: Path, monkeypatch) -> None:
    """Free tiers wobble. Crying wolf on every blip trains the owner to ignore it."""
    root = _init_repo(tmp_path, ["alpha"])
    monkeypatch.setattr(run, "get_provider", lambda name: _Raises(ProviderError("down")))

    assert run.main(["--repo-root", str(root), "--provider", "raiser", "--no-push"]) == 0


def test_an_outage_that_never_ends_stops_looking_healthy(tmp_path: Path, monkeypatch) -> None:
    """A revoked key used to look exactly like a working project: green, forever."""
    root = _init_repo(tmp_path, ["alpha"])
    monkeypatch.setattr(run, "get_provider", lambda name: _Raises(ProviderError("revoked")))
    run.main(["--repo-root", str(root), "--provider", "raiser", "--no-push"])

    state_path = root / ".forge" / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    long_ago = datetime.now(timezone.utc) - timedelta(days=run.OUTAGE_GRACE_DAYS + 1)
    state[run._OUTAGE_KEY] = long_ago.isoformat()
    state_path.write_text(json.dumps(state), encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=root, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "s"], cwd=root, capture_output=True)

    assert run.main(["--repo-root", str(root), "--provider", "raiser", "--no-push"]) == 1


def test_the_outage_clock_resets_once_the_provider_answers(tmp_path: Path, monkeypatch) -> None:
    """Otherwise one old outage makes the next brief one look permanent."""
    root = _init_repo(tmp_path, ["alpha"])
    state_path = root / ".forge" / "state.json"
    state_path.parent.mkdir(exist_ok=True)
    long_ago = datetime.now(timezone.utc) - timedelta(days=run.OUTAGE_GRACE_DAYS + 5)
    state_path.write_text(json.dumps({run._OUTAGE_KEY: long_ago.isoformat()}), encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=root, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "s"], cwd=root, capture_output=True)
    monkeypatch.setattr(run, "get_provider", lambda name: _Raises(TruncatedResponse("cut off")))

    run.main(["--repo-root", str(root), "--provider", "raiser", "--no-push"])

    assert run._OUTAGE_KEY not in json.loads(state_path.read_text(encoding="utf-8"))


def test_a_cut_off_answer_is_a_counted_attempt_not_an_outage(tmp_path: Path, monkeypatch) -> None:
    """An outage is retried forever without counting. A reply that will never fit
    would therefore stall the loop in silence, so it has to be an attempt."""
    root = _init_repo(tmp_path, ["alpha"])
    monkeypatch.setattr(run, "get_provider", lambda name: _Raises(TruncatedResponse("cut off")))

    run.main(["--repo-root", str(root), "--provider", "raiser", "--no-push"])

    state = json.loads((root / ".forge" / "state.json").read_text(encoding="utf-8"))
    assert state.get("alpha") == 1
    assert "cut off" in (root / "DEVLOG.md").read_text(encoding="utf-8")


def test_a_truncated_completion_is_recognised() -> None:
    """The provider says so in finish_reason; nothing used to read it."""
    body = {"choices": [{"finish_reason": "length", "message": {"content": "def f(:"}}]}
    with pytest.raises(TruncatedResponse):
        llm._extract_completion(body)


def test_the_request_asks_for_an_explicit_completion_budget() -> None:
    """Without one the provider picks, and a growing file rewrite runs past it."""
    assert llm._MAX_COMPLETION_TOKENS > 4096


def test_a_flooding_check_is_stopped_instead_of_eating_the_runner(tmp_path: Path) -> None:
    """Measured before this existed: 400 MB of child output cost 1.8 GB resident.

    The orchestrator is killed by the OOM reaper rather than raising, so it never
    reverts and never records the attempt -- and the attempt count is committed, so
    the next run picks the same task and does it again.
    """
    started = time.monotonic()
    ok, log = guardrail._run(
        "flood",
        [sys.executable, "-c", "while True: print('x' * 100000)"],
        tmp_path,
    )
    elapsed = time.monotonic() - started

    assert ok is False
    assert "flooded its output" in log
    assert elapsed < guardrail.CHECK_TIMEOUT_SECONDS / 2
    assert len(log) < guardrail.OUTPUT_LIMIT_BYTES


def test_a_flooding_collection_is_unknown_not_empty(tmp_path: Path, monkeypatch) -> None:
    """Returning 0 would read as the whole suite vanishing, which is a hard reject."""
    monkeypatch.setattr(
        guardrail, "_drain", lambda label, args, cwd: (None, "partial output", True)
    )

    assert guardrail.count_tests(tmp_path) == -1


def test_a_normal_failure_still_reports_its_output(tmp_path: Path) -> None:
    """Capping output is worthless if it costs the model the error it must fix."""
    ok, log = guardrail._run(
        "boom",
        [sys.executable, "-c", "import sys; print('the reason'); sys.exit(1)"],
        tmp_path,
    )

    assert ok is False
    assert "the reason" in log
