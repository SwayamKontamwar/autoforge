"""A patch that cannot even be written to disk must not wedge the loop.

The model chooses both file paths and file contents, so applying a patch can raise
in ways no allowlist predicts: a module written where a package directory already
exists, a name the filesystem rejects, a path that is too long. If that exception
escapes it does so *before* the revert and *before* the attempt is recorded, which
leaves the tree dirty and the attempt count unchanged -- so the same task is picked
again, and crashes again, on every future run. These tests pin the behaviour that
turns such a crash into an ordinary failed attempt.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from builder import run
from builder.guardrail import GuardrailResult
from builder.llm import File, Patch

from .test_run import _init_repo, _is_clean, _ScriptedProvider


def _boom(*args, **kwargs):
    raise IsADirectoryError(21, "Is a directory")


def test_an_unwritable_patch_fails_instead_of_raising(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(run, "_apply", _boom)
    patch = Patch(files=[File("app/thing.py", "x = 1\n")], summary="s")

    result = run._judge(tmp_path, patch)

    assert result.ok is False


def test_the_failure_log_names_the_error_and_the_paths(tmp_path: Path, monkeypatch) -> None:
    """This log is fed back to the model, so it has to say what to change."""
    monkeypatch.setattr(run, "_apply", _boom)
    patch = Patch(files=[File("app/thing.py", "x = 1\n")], summary="s")

    result = run._judge(tmp_path, patch)

    assert "IsADirectoryError" in result.log
    assert "app/thing.py" in result.log


def test_a_crashing_baseline_is_reported_not_raised(tmp_path: Path, monkeypatch) -> None:
    """The baseline check decides "broken environment" vs "bad patch"; it must answer."""
    monkeypatch.setattr(run, "run_guardrail", _boom)

    assert run._baseline(tmp_path).ok is False


def test_an_unmeasurable_suite_is_unknown_not_empty(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(run, "count_tests", _boom)

    assert run._safe_count_tests(tmp_path) == -1


def test_a_patch_that_collides_with_a_directory_counts_as_an_attempt(
    tmp_path: Path, monkeypatch
) -> None:
    """End to end: the real failure, on a real repo, with real filesystem semantics."""
    root = _init_repo(tmp_path, ["do the thing"])
    (root / "app" / "pkg").mkdir()
    (root / "app" / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-qm", "pkg"], cwd=root, check=True, capture_output=True)

    # A file at a path that is already a directory: write_text cannot do this.
    patch = Patch(files=[File("app/pkg", "y = 2\n")], summary="collide")
    monkeypatch.setattr(run, "get_provider", lambda name: _ScriptedProvider(patch))
    monkeypatch.setattr(run, "run_guardrail", lambda r: GuardrailResult(ok=True, log="stub"))

    rc = run.main(["--repo-root", str(root), "--provider", "scripted", "--no-push"])

    assert rc == 0
    assert _is_clean(root)
    state = run._load_state(root / ".forge" / "state.json")
    assert state.get("do the thing") == 1
