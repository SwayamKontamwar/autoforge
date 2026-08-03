"""The suite must keep passing as the bot makes progress.

A test that asserts a backlog line is still unfinished passes today and fails the
moment the bot builds that task. That is not a normal test failure. A clean tree
that fails the guardrail is read as a broken environment rather than a bad patch,
so every scheduled run from then on declines to work and commits a blocked-task
note instead -- forever, silently, with nobody watching. Succeeding is what breaks
it, which is why it survives review: everything is green right up until it works.

That happened twice. So rather than trusting the next author to remember, the
future is simulated: the whole suite runs again against a backlog where every task
is already done. Anything coupled to the backlog being unfinished fails here, now,
while it is still a normal red test.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
_GUARD = "FORGE_PROGRESS_SIM"
_SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}


@pytest.mark.skipif(
    os.environ.get(_GUARD) == "1",
    reason="inner run of the simulation; recursing would never terminate",
)
def test_the_suite_survives_every_task_being_finished(tmp_path):
    work = tmp_path / "repo"
    shutil.copytree(
        REPO_ROOT,
        work,
        ignore=lambda _, names: [n for n in names if n in _SKIP_DIRS],
        symlinks=True,
    )

    backlog = work / "BACKLOG.md"
    original = backlog.read_text(encoding="utf-8")
    assert "- [ ]" in original, "nothing left to simulate; this test has gone stale"
    backlog.write_text(original.replace("- [ ]", "- [x]"), encoding="utf-8")

    env = {**os.environ, _GUARD: "1", "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-x"],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        "The suite fails once every backlog task is marked done. A test is asserting "
        "that work is still outstanding, which will wedge the build the moment the "
        "bot finishes that task.\n\n" + proc.stdout[-3000:] + proc.stderr[-2000:]
    )
