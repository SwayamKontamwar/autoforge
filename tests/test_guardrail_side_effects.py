"""Regressions for damage done by the checks themselves, not by the patch.

The guardrail does not read generated code, it runs it: ruff, an import of the app
and pytest all execute with the repository as their working directory. So a patch
that only writes inside ``tests/`` can still reach ``BACKLOG.md``, ``DEVLOG.md`` and
the repository root while it is being checked -- outside what the revert restores and
inside what ``git add -A`` commits.

Reproduced against the code as it then stood: a test that rewrote ``BACKLOG.md`` and
passed took the backlog from 1032 open tasks to none, crashed the run with an
``IndexError``, and committed the wreckage. A quieter variant is worse: a rewrite
that merely shifts line numbering leaves the run green while the wrong task is ticked
off, so the real one is handed out again forever.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from builder import backlog, run
from builder.guardrail import GuardrailResult
from builder.llm import File, Patch

from .test_run import _init_repo


def test_a_check_may_not_rewrite_the_backlog(tmp_path: Path) -> None:
    root = _init_repo(tmp_path, ["alpha", "beta"])
    (root / "BACKLOG.md").write_text("# Backlog\n", encoding="utf-8")

    run._restore_outside_patch_area(root)

    assert backlog.open_count(root / "BACKLOG.md") == 2


def test_a_check_may_not_delete_a_tracked_file(tmp_path: Path) -> None:
    root = _init_repo(tmp_path, ["alpha"])
    (root / "BACKLOG.md").unlink()

    run._restore_outside_patch_area(root)

    assert (root / "BACKLOG.md").exists()


def test_a_check_may_not_leave_litter_in_the_repository(tmp_path: Path) -> None:
    root = _init_repo(tmp_path, ["alpha"])
    (root / "leftover.json").write_text("{}", encoding="utf-8")
    (root / "sub").mkdir()
    (root / "sub" / "deep.txt").write_text("x", encoding="utf-8")

    run._restore_outside_patch_area(root)

    assert not (root / "leftover.json").exists()
    assert not (root / "sub" / "deep.txt").exists()


def test_the_patch_itself_survives_the_restore(tmp_path: Path) -> None:
    """The cleanup has to be blind to intent, so it must be scoped by path instead."""
    root = _init_repo(tmp_path, ["alpha"])
    (root / "app" / "main.py").write_text("x = 2\n", encoding="utf-8")
    (root / "tests" / "test_new.py").write_text(
        "def test_x() -> None:\n    pass\n", encoding="utf-8"
    )

    run._restore_outside_patch_area(root)

    assert (root / "app" / "main.py").read_text(encoding="utf-8") == "x = 2\n"
    assert (root / "tests" / "test_new.py").exists()


def test_a_passing_patch_does_not_ship_a_wrecked_backlog(tmp_path: Path, monkeypatch) -> None:
    """The end-to-end shape of the original failure, without waiting on real pytest."""
    root = _init_repo(tmp_path, ["alpha", "beta"])
    patch = Patch(
        files=[File("tests/test_report.py", "def test_x() -> None:\n    pass\n")],
        summary="s",
    )

    def _wrecks_the_backlog(repo_root: Path) -> GuardrailResult:
        (repo_root / "BACKLOG.md").write_text("# Backlog\n", encoding="utf-8")
        return GuardrailResult(ok=True, log="")

    monkeypatch.setattr(run, "run_guardrail", _wrecks_the_backlog)
    monkeypatch.setattr(run, "_autofix", lambda repo_root, patch: None)

    result = run._judge(root, patch)

    assert result.ok
    assert backlog.open_count(root / "BACKLOG.md") == 2
    assert (root / "tests" / "test_report.py").exists()


def test_counting_tests_cannot_wreck_the_backlog_either(tmp_path: Path, monkeypatch) -> None:
    """Collection imports every test module, so it runs repository code too."""
    root = _init_repo(tmp_path, ["alpha", "beta"])

    def _wrecks_the_backlog(repo_root: Path) -> int:
        (repo_root / "BACKLOG.md").write_text("# Backlog\n", encoding="utf-8")
        return 3

    monkeypatch.setattr(run, "count_tests", _wrecks_the_backlog)

    assert run._safe_count_tests(root) == 3
    assert backlog.open_count(root / "BACKLOG.md") == 2


def test_a_stale_index_never_corrupts_an_unrelated_line(tmp_path: Path) -> None:
    """``partition`` on a non-task line welds ``- [x]`` onto whatever was there.

    The old code would have turned the heading into ``# Backlog- [x]`` and left the
    real task open, so it would be handed out again on every future run.
    """
    path = tmp_path / "BACKLOG.md"
    path.write_text("# Backlog\n- [ ] alpha\n", encoding="utf-8")

    backlog.mark_done(path, 0, expect="alpha")

    assert path.read_text(encoding="utf-8") == "# Backlog\n- [x] alpha\n"


def test_marking_refuses_when_it_cannot_tell_which_line_was_meant(tmp_path: Path) -> None:
    path = tmp_path / "BACKLOG.md"
    path.write_text("# Backlog\n- [ ] alpha\n", encoding="utf-8")

    with pytest.raises(ValueError):
        backlog.mark_done(path, 0)

    assert path.read_text(encoding="utf-8") == "# Backlog\n- [ ] alpha\n"


def test_marking_relocates_a_task_whose_line_moved(tmp_path: Path) -> None:
    path = tmp_path / "BACKLOG.md"
    path.write_text("# Backlog\n- [ ] alpha\n- [ ] beta\n", encoding="utf-8")

    backlog.mark_done(path, 1, expect="beta")

    text = path.read_text(encoding="utf-8")
    assert "- [x] beta" in text
    assert "- [ ] alpha" in text


def test_marking_refuses_a_task_that_is_no_longer_open(tmp_path: Path) -> None:
    path = tmp_path / "BACKLOG.md"
    path.write_text("# Backlog\n- [x] alpha\n", encoding="utf-8")

    with pytest.raises(ValueError):
        backlog.mark_done(path, 1, expect="alpha")


def test_a_stale_index_does_not_strand_the_run(tmp_path: Path, capsys) -> None:
    """A task that is no longer open needs no tick, so the run must finish normally."""
    path = tmp_path / "BACKLOG.md"
    path.write_text("# Backlog\n- [x] alpha\n", encoding="utf-8")

    run._mark_done(path, backlog.Task(index=1, text="alpha"))

    assert "could not tick the task off" in capsys.readouterr().err


def test_archiving_never_overwrites_an_existing_archive(tmp_path: Path) -> None:
    """Numbering off a file count points back at a file whenever the sequence has a gap."""
    path = tmp_path / "BACKLOG.md"
    path.write_text("# Backlog\n", encoding="utf-8")
    archive = tmp_path / "docs" / "backlog"
    archive.mkdir(parents=True)
    (archive / "completed-001.md").write_text("first", encoding="utf-8")
    (archive / "completed-003.md").write_text("third", encoding="utf-8")

    chosen = backlog._next_archive_path(path)

    assert not chosen.exists()
    assert (archive / "completed-001.md").read_text(encoding="utf-8") == "first"
    assert (archive / "completed-003.md").read_text(encoding="utf-8") == "third"


def test_the_rebase_retry_carries_a_git_identity(tmp_path: Path, monkeypatch) -> None:
    """A runner has no configured user, so an identity-less rebase fatals every time."""
    root = _init_repo(tmp_path, ["alpha"])
    seen: list[list[str]] = []

    def _fake(repo_root: Path, *args: str, check: bool = True):
        seen.append(list(args))
        if args[0] == "rev-parse":
            return subprocess.CompletedProcess(args, 0, "main\n", "")
        if "push" in args:
            return subprocess.CompletedProcess(args, 1, "", "rejected")
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(run, "_git", _fake)
    run._push(root, attempts=2)

    rebases = [a for a in seen if "pull" in a]
    assert rebases, "expected a rebase retry"
    assert any(arg.startswith("user.email=") for arg in rebases[0])


def test_a_commit_that_cannot_be_pushed_reports_failure(tmp_path: Path, monkeypatch) -> None:
    """An unpushed commit dies with the runner, and silence eventually kills the schedule."""
    root = _init_repo(tmp_path, ["alpha"])
    (root / "app" / "main.py").write_text("x = 2\n", encoding="utf-8")
    monkeypatch.setattr(run, "_push", lambda repo_root, attempts=3: False)

    assert run._commit(root, "forge: x", push=True) is False


def test_committing_nothing_is_not_a_failure(tmp_path: Path) -> None:
    root = _init_repo(tmp_path, ["alpha"])

    assert run._commit(root, "forge: x", push=False) is True
