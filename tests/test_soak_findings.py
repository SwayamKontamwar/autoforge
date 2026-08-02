"""Everything here was found by a soak that wrecked the repository and killed the
loop mid-run, not by reading the code.

Two of these are permanent wedges rather than one-off crashes. `.forge/state.json`
is committed, so a bad *shape* inside it (not just bad JSON) came back on every
future checkout and raised in the same place forever. And a run killed between
writing a patch and judging it left the files behind, so on the local
cron/launchd setup the README suggests, every later run saw a dirty tree and
refused -- silently, until a human noticed.
"""

import json
import subprocess
from pathlib import Path

import pytest

from builder import run


def _repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "app").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "BACKLOG.md").write_text("# Backlog\n\n- [ ] Do a thing\n", encoding="utf-8")
    (tmp_path / "DEVLOG.md").write_text("# Devlog\n", encoding="utf-8")
    (tmp_path / "app" / "keep.py").write_text("KEEP = 1\n", encoding="utf-8")
    for cmd in (
        ["git", "add", "-A"],
        ["git", "-c", "user.email=t@x", "-c", "user.name=t", "commit", "-qm", "init"],
    ):
        subprocess.run(cmd, cwd=tmp_path, check=True)
    return tmp_path


# --- committed state of the wrong shape -------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        {"__last_failures__": "not-a-dict"},
        {"__last_failures__": ["a", "b"]},
        {"__last_failures__": 7},
        {"__outage_since__": 12345},
        {"__outage_since__": {"since": "yesterday"}},
        {"some task": "three"},
        {"some task": None},
        {"some task": [1, 2]},
        {"some task": {"count": 1}},
        {"some task": True},
    ],
)
def test_state_of_the_wrong_shape_never_reaches_the_rest_of_the_run(tmp_path, payload):
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(payload), encoding="utf-8")

    state = run._load_state(state_path)

    # Whatever survives must be usable by every reader without raising.
    run._remember_failure(state, "some task", "boom")
    run._forget_failure(state, "some task")
    assert isinstance(run._previous_failure(state, "some task"), str)
    assert isinstance(int(state.get("some task", 0)), int)
    run._close_task_state(state, "some task")
    run._outage_started(state)


def test_a_string_where_a_failure_map_belongs_does_not_crash_the_run():
    """The exact AttributeError the soak hit: 'str' object has no attribute 'pop'."""
    cleaned = run._sanitize_state({"__last_failures__": "not-a-dict", "a task": 2})

    run._forget_failure(cleaned, "a task")
    run._remember_failure(cleaned, "a task", "boom")

    assert cleaned["a task"] == 2
    assert isinstance(cleaned["__last_failures__"], dict)


def test_usable_state_survives_untouched():
    original = {
        "a task": 2,
        "__last_failures__": {"a task": "traceback text"},
        "__outage_since__": "2026-01-01T00:00:00+00:00",
    }
    assert run._sanitize_state(dict(original)) == original


# --- a run killed between writing a patch and judging it --------------------


def test_files_from_an_interrupted_run_are_cleaned_up_not_left_to_wedge(tmp_path):
    repo = _repo(tmp_path)
    run._begin_inflight(repo)
    (repo / "app" / "half_written.py").write_text("def broken(:\n", encoding="utf-8")
    (repo / "app" / "keep.py").write_text("KEEP = 999\n", encoding="utf-8")

    assert not run._is_clean(repo)
    assert run._recover_interrupted_run(repo) is True

    assert run._is_clean(repo), "the next run would abort on a dirty tree forever"
    assert not (repo / "app" / "half_written.py").exists()
    assert (repo / "app" / "keep.py").read_text(encoding="utf-8") == "KEEP = 1\n"
    assert not run._inflight_path(repo).exists()


def test_a_dirty_tree_without_the_marker_is_still_refused(tmp_path):
    """Someone's work in progress is not ours to delete."""
    repo = _repo(tmp_path)
    (repo / "app" / "human_edit.py").write_text("WIP = True\n", encoding="utf-8")

    assert run._recover_interrupted_run(repo) is False
    assert (repo / "app" / "human_edit.py").exists()


def test_the_marker_is_cleared_before_anything_could_commit_it(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    run._begin_inflight(repo)
    assert run._inflight_path(repo).exists()

    staged = []
    real_git = run._git

    def spy(root, *args, **kwargs):
        if args[:1] == ("add",):
            staged.append(run._inflight_path(repo).exists())
        return real_git(root, *args, **kwargs)

    monkeypatch.setattr(run, "_git", spy)
    run._commit(repo, "forge: something", push=False)

    assert staged == [False], "the marker still existed when files were staged"
    assert not run._inflight_path(repo).exists()


def test_the_marker_is_gitignored():
    root = Path(__file__).resolve().parent.parent
    assert ".forge/inflight" in (root / ".gitignore").read_text(encoding="utf-8")


# --- a repository the loop cannot work on -----------------------------------


def test_missing_backlog_is_explained_not_a_traceback(tmp_path, capsys):
    repo = _repo(tmp_path)
    (repo / "BACKLOG.md").unlink()

    assert run.main(["--provider", "mock", "--repo-root", str(repo), "--no-push"]) == 1
    assert "BACKLOG.md is missing" in capsys.readouterr().err


def test_backlog_that_is_a_directory_is_explained(tmp_path, capsys):
    repo = _repo(tmp_path)
    (repo / "BACKLOG.md").unlink()
    (repo / "BACKLOG.md").mkdir()

    assert run.main(["--provider", "mock", "--repo-root", str(repo), "--no-push"]) == 1
    assert "not a regular file" in capsys.readouterr().err


def test_forge_that_is_a_file_is_explained(tmp_path, capsys):
    repo = _repo(tmp_path)
    (repo / ".forge").write_text("i am not a directory", encoding="utf-8")

    assert run.main(["--provider", "mock", "--repo-root", str(repo), "--no-push"]) == 1
    assert ".forge exists but is not a directory" in capsys.readouterr().err


def test_devlog_that_is_a_directory_is_explained(tmp_path, capsys):
    repo = _repo(tmp_path)
    (repo / "DEVLOG.md").unlink()
    (repo / "DEVLOG.md").mkdir()

    assert run.main(["--provider", "mock", "--repo-root", str(repo), "--no-push"]) == 1
    assert "DEVLOG.md is not a regular file" in capsys.readouterr().err
