"""Orchestrator autonomy tests.

These exercise ``builder.run.main`` end to end against a real temporary git repo,
with the model provider and the guardrail stubbed so the test is fast and
hermetic. They lock down the promises the unattended loop must keep: it never
leaves a dirty tree, it advances or safely skips every task, and it records
honest state for each outcome.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from builder import run
from builder.guardrail import GuardrailResult
from builder.llm import File, Patch


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)


def _init_repo(tmp_path: Path, tasks: list[str]) -> Path:
    root = tmp_path / "repo"
    (root / "app").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "app" / "__init__.py").write_text("", encoding="utf-8")
    (root / "app" / "main.py").write_text("x = 1\n", encoding="utf-8")
    (root / "tests" / "__init__.py").write_text("", encoding="utf-8")
    lines = "\n".join(f"- [ ] {t}" for t in tasks)
    (root / "BACKLOG.md").write_text(f"# Backlog\n{lines}\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "t")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "seed")
    return root


def _is_clean(root: Path) -> bool:
    out = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True
    ).stdout
    return out.strip() == ""


class _ScriptedProvider:
    """Returns a preset patch (or raises) so we can drive each code path."""

    def __init__(self, patch: Patch) -> None:
        self._patch = patch

    def generate(self, task: str, context: str) -> Patch:
        return self._patch


def _run(monkeypatch, root: Path, patch: Patch, guardrail_ok: bool, max_attempts: int = 3) -> int:
    monkeypatch.setattr(run, "get_provider", lambda name: _ScriptedProvider(patch))

    def _stub(repo_root: Path) -> GuardrailResult:
        # Model reality: a clean checkout is always green, so only a tree that still
        # has the generated files applied can fail. Without this the revert path would
        # look identical to a broken build environment, which is a different bug.
        applied = any((repo_root / f.path).exists() for f in patch.files)
        return GuardrailResult(ok=guardrail_ok if applied else True, log="stub")

    monkeypatch.setattr(run, "run_guardrail", _stub)
    return run.main(
        ["--repo-root", str(root), "--provider", "scripted", "--no-push",
         "--max-attempts", str(max_attempts)]
    )


def test_success_marks_done_and_stays_clean(tmp_path, monkeypatch) -> None:
    root = _init_repo(tmp_path, ["do the thing"])
    good = Patch(files=[File("app/feature.py", "y = 2\n")], summary="add feature")
    assert _run(monkeypatch, root, good, guardrail_ok=True) == 0
    assert _is_clean(root)
    assert "- [x] do the thing" in (root / "BACKLOG.md").read_text(encoding="utf-8")
    assert (root / "app" / "feature.py").exists()


def test_broken_patch_is_reverted_and_task_stays_open(tmp_path, monkeypatch) -> None:
    root = _init_repo(tmp_path, ["do the thing"])
    patch = Patch(files=[File("app/feature.py", "y = 2\n")], summary="attempt")
    assert _run(monkeypatch, root, patch, guardrail_ok=False) == 0
    assert _is_clean(root)
    assert "- [ ] do the thing" in (root / "BACKLOG.md").read_text(encoding="utf-8")
    assert not (root / "app" / "feature.py").exists()  # reverted


def test_failing_patch_skips_after_max_attempts(tmp_path, monkeypatch) -> None:
    """Bad model code must still burn attempts and free the backlog — unlike a bad env."""
    root = _init_repo(tmp_path, ["do the thing"])
    patch = Patch(files=[File("app/feature.py", "y = 2\n")], summary="attempt")
    for _ in range(3):
        assert _run(monkeypatch, root, patch, guardrail_ok=False, max_attempts=3) == 0
        assert _is_clean(root)
    text = (root / "BACKLOG.md").read_text(encoding="utf-8")
    assert "- [x] do the thing" in text
    assert "skipped after 3 failed attempts" in text


def test_out_of_bounds_patch_skips_after_max_attempts(tmp_path, monkeypatch) -> None:
    root = _init_repo(tmp_path, ["do the thing"])
    bad = Patch(files=[File("builder/evil.py", "boom = 1\n")], summary="escape")
    for _ in range(3):
        assert _run(monkeypatch, root, bad, guardrail_ok=True, max_attempts=3) == 0
        assert _is_clean(root)
        assert not (root / "builder" / "evil.py").exists()  # never applied
    text = (root / "BACKLOG.md").read_text(encoding="utf-8")
    assert "- [x] do the thing" in text
    assert "skipped after 3 out-of-bounds patches" in text


def test_provider_error_is_logged_without_touching_code(tmp_path, monkeypatch) -> None:
    root = _init_repo(tmp_path, ["do the thing"])

    class _Boom:
        def generate(self, task: str, context: str) -> Patch:
            raise run.ProviderError("down")

    monkeypatch.setattr(run, "get_provider", lambda name: _Boom())
    assert run.main(["--repo-root", str(root), "--provider", "x", "--no-push"]) == 0
    assert _is_clean(root)
    assert "- [ ] do the thing" in (root / "BACKLOG.md").read_text(encoding="utf-8")
    assert "blocked" in (root / "DEVLOG.md").read_text(encoding="utf-8")


def test_repeated_provider_outage_is_logged_only_once(tmp_path, monkeypatch) -> None:
    """A months-long outage must not bury the log under identical blocked commits."""
    root = _init_repo(tmp_path, ["do the thing"])

    class _Boom:
        def generate(self, task: str, context: str) -> Patch:
            raise run.ProviderError("down")

    monkeypatch.setattr(run, "get_provider", lambda name: _Boom())

    def _count() -> int:
        out = subprocess.run(
            ["git", "log", "--pretty=%s"], cwd=root, capture_output=True, text=True, check=True
        ).stdout
        return out.count("forge: log blocked task")

    for _ in range(4):
        assert run.main(["--repo-root", str(root), "--provider", "x", "--no-push"]) == 0

    assert _count() == 1
    assert _is_clean(root)
    # The task is untouched and still queued for when the provider recovers.
    assert "- [ ] do the thing" in (root / "BACKLOG.md").read_text(encoding="utf-8")


def test_stale_outage_is_relogged_to_keep_the_schedule_alive(tmp_path, monkeypatch) -> None:
    """GitHub disables cron after 60 days idle, so a long outage must still heartbeat."""
    root = _init_repo(tmp_path, ["do the thing"])

    class _Boom:
        def generate(self, task: str, context: str) -> Patch:
            raise run.ProviderError("down")

    monkeypatch.setattr(run, "get_provider", lambda name: _Boom())

    def _blocked_count() -> int:
        out = subprocess.run(
            ["git", "log", "--pretty=%s"], cwd=root, capture_output=True, text=True, check=True
        ).stdout
        return out.count("forge: log blocked task")

    run.main(["--repo-root", str(root), "--provider", "x", "--no-push"])
    assert _blocked_count() == 1

    # Still inside the heartbeat window: stay quiet.
    run.main(["--repo-root", str(root), "--provider", "x", "--no-push"])
    assert _blocked_count() == 1

    # Pretend the outage note is older than the heartbeat window.
    monkeypatch.setattr(run, "HEARTBEAT_DAYS", 0)
    run.main(["--repo-root", str(root), "--provider", "x", "--no-push"])
    assert _blocked_count() == 2
    assert _is_clean(root)


def test_broken_environment_does_not_consume_the_backlog(tmp_path, monkeypatch) -> None:
    """A bad checkout must not burn attempts and skip every task in the backlog."""
    root = _init_repo(tmp_path, ["do the thing"])
    patch = Patch(files=[File("app/feature.py", "y = 2\n")], summary="add feature")

    class _Provider:
        def generate(self, task: str, context: str) -> Patch:
            return patch

    monkeypatch.setattr(run, "get_provider", lambda name: _Provider())
    # Fails both with the patch applied and on a clean tree: the environment is broken.
    monkeypatch.setattr(run, "run_guardrail", lambda r: GuardrailResult(ok=False, log="boom"))

    for _ in range(5):
        assert run.main(["--repo-root", str(root), "--provider", "x", "--no-push"]) == 0

    # The task survives: not skipped, no attempts recorded, nothing half-applied.
    assert "- [ ] do the thing" in (root / "BACKLOG.md").read_text(encoding="utf-8")
    assert not (root / "app" / "feature.py").exists()
    assert _is_clean(root)
    state_file = root / ".forge" / "state.json"
    if state_file.exists():
        assert json.loads(state_file.read_text(encoding="utf-8")).get("do the thing") in (None, 0)
    # And the outage is recorded once, not five times.
    subjects = subprocess.run(
        ["git", "log", "--pretty=%s"], cwd=root, capture_output=True, text=True, check=True
    ).stdout
    assert subjects.count("environment unavailable") == 1


def test_dirty_tree_aborts(tmp_path, monkeypatch) -> None:
    root = _init_repo(tmp_path, ["do the thing"])
    (root / "app" / "stray.py").write_text("z = 3\n", encoding="utf-8")
    good = Patch(files=[File("app/feature.py", "y = 2\n")], summary="add feature")
    assert _run(monkeypatch, root, good, guardrail_ok=True) == 1


def test_autofix_repairs_fixable_lint(tmp_path) -> None:
    root = _init_repo(tmp_path, ["do the thing"])
    # `os` is imported but unused (F401) and imports are unsorted (I001) — both safe autofixes.
    messy = "import sys\nimport os\n\n\ndef version() -> str:\n    return sys.version\n"
    (root / "app" / "messy.py").write_text(messy, encoding="utf-8")
    run._autofix(root, Patch(files=[File("app/messy.py", messy)], summary="x"))
    fixed = (root / "app" / "messy.py").read_text(encoding="utf-8")
    assert "import os" not in fixed  # unused import stripped by `ruff check --fix`


class _RecordingProvider:
    """Captures the context it was handed so we can assert on what the model sees."""

    def __init__(self, patch: Patch) -> None:
        self._patch = patch
        self.contexts: list[str] = []

    def generate(self, task: str, context: str) -> Patch:
        self.contexts.append(context)
        return self._patch


def _run_recording(monkeypatch, root: Path, provider, guardrail_ok: bool, max_attempts: int = 3):
    monkeypatch.setattr(run, "get_provider", lambda name: provider)

    def _stub(repo_root: Path) -> GuardrailResult:
        applied = any((repo_root / f.path).exists() for f in provider._patch.files)
        return GuardrailResult(
            ok=guardrail_ok if applied else True,
            log="E   AssertionError: LinkOut.url expected str",
        )

    monkeypatch.setattr(run, "run_guardrail", _stub)
    return run.main(
        ["--repo-root", str(root), "--provider", "scripted", "--no-push",
         "--max-attempts", str(max_attempts)]
    )


def test_guardrail_failure_is_fed_back_into_the_next_attempt(tmp_path, monkeypatch) -> None:
    """A retry that cannot see the last failure is just the same roll of the dice.

    Every attempt would otherwise get a byte-identical prompt, reproduce the same
    mistake, and burn the task's attempts until it is skipped — abandoning work that
    was one correction away. Proven against a live model: two blind attempts failed
    identically, and the attempt that received the traceback shipped.
    """
    root = _init_repo(tmp_path, ["do the thing"])
    bad = Patch(files=[File("app/feature.py", "y = 2\n")], summary="add feature")

    first = _RecordingProvider(bad)
    assert _run_recording(monkeypatch, root, first, guardrail_ok=False) == 0
    assert "previous attempt" not in first.contexts[0].lower(), "nothing to feed back yet"

    second = _RecordingProvider(bad)
    assert _run_recording(monkeypatch, root, second, guardrail_ok=False) == 0
    prompt = second.contexts[0]
    assert "previous attempt" in prompt.lower()
    assert "LinkOut.url expected str" in prompt, "the actual failure must reach the model"
    assert _is_clean(root)


def test_feedback_is_dropped_once_the_task_succeeds(tmp_path, monkeypatch) -> None:
    root = _init_repo(tmp_path, ["do the thing"])
    patch = Patch(files=[File("app/feature.py", "y = 2\n")], summary="add feature")

    assert _run_recording(monkeypatch, root, _RecordingProvider(patch), guardrail_ok=False) == 0
    state = json.loads((root / ".forge" / "state.json").read_text(encoding="utf-8"))
    assert state.get("__last_failures__"), "a failure should have been remembered"

    assert _run_recording(monkeypatch, root, _RecordingProvider(patch), guardrail_ok=True) == 0
    state = json.loads((root / ".forge" / "state.json").read_text(encoding="utf-8"))
    assert not state.get("__last_failures__"), "stale traceback outlived the task"
    assert _is_clean(root)


def test_feedback_is_dropped_when_the_task_is_skipped(tmp_path, monkeypatch) -> None:
    """Skipped tasks never run again, so keeping their tracebacks only grows the file."""
    root = _init_repo(tmp_path, ["do the thing"])
    bad = Patch(files=[File("app/feature.py", "y = 2\n")], summary="add feature")
    for _ in range(2):
        assert _run_recording(
            monkeypatch, root, _RecordingProvider(bad), guardrail_ok=False, max_attempts=2
        ) == 0
    assert "- [x] do the thing" in (root / "BACKLOG.md").read_text(encoding="utf-8")
    state = json.loads((root / ".forge" / "state.json").read_text(encoding="utf-8"))
    assert not state.get("__last_failures__")
    assert _is_clean(root)


def _remote_log(remote: Path) -> str:
    """Read a bare repo's history without cd-ing into it (safe.bareRepository)."""
    return subprocess.run(
        ["git", f"--git-dir={remote}", "log", "--oneline", "--all"],
        capture_output=True, text=True, check=True,
    ).stdout


def test_push_rebases_when_the_remote_moved(tmp_path) -> None:
    """A rejected push would throw away work that already passed the guardrail.

    The bot only pushes after the guardrail is green, so a push that fails takes
    finished, verified code with it and fails the run red. Anyone pushing between
    this job's checkout and its push causes it, which over years is a matter of
    time. Uses a real bare remote rather than a stubbed git.
    """
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)

    root = _init_repo(tmp_path, ["do the thing"])
    _git(root, "remote", "add", "origin", str(remote))
    _git(root, "push", "-q", "origin", "HEAD")

    # Somebody else pushes while this run is working.
    other = tmp_path / "other"
    subprocess.run(["git", "clone", "-q", str(remote), str(other)], check=True)
    _git(other, "config", "user.email", "o@example.com")
    _git(other, "config", "user.name", "o")
    (other / "HUMAN.md").write_text("a human was here\n", encoding="utf-8")
    _git(other, "add", "-A")
    _git(other, "commit", "-qm", "human change")
    _git(other, "push", "-q", "origin", "HEAD")

    (root / "app" / "feature.py").write_text("y = 2\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "forge: add feature")

    assert run._push(root) is True

    log = _remote_log(remote)
    assert "forge: add feature" in log, "the bot's work must reach the remote"
    assert "human change" in log, "the human's commit must not be clobbered"


def test_push_refuses_to_clobber_on_a_real_conflict(tmp_path) -> None:
    """Losing one run's work is recoverable; force-pushing over a human is not."""
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-q", str(remote)], check=True)
    root = _init_repo(tmp_path, ["do the thing"])
    _git(root, "remote", "add", "origin", str(remote))
    _git(root, "push", "-q", "origin", "HEAD")

    other = tmp_path / "other"
    subprocess.run(["git", "clone", "-q", str(remote), str(other)], check=True)
    _git(other, "config", "user.email", "o@example.com")
    _git(other, "config", "user.name", "o")
    (other / "app" / "clash.py").write_text("human = 1\n", encoding="utf-8")
    _git(other, "add", "-A")
    _git(other, "commit", "-qm", "human edits clash")
    _git(other, "push", "-q", "origin", "HEAD")

    (root / "app" / "clash.py").write_text("bot = 2\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "forge: bot edits clash")

    assert run._push(root) is False
    log = _remote_log(remote)
    assert "human edits clash" in log
    assert "forge: bot edits clash" not in log
    assert _is_clean(root), "a failed push must not leave a half-rebased tree"


def test_finished_tasks_leave_nothing_behind_in_state(tmp_path, monkeypatch) -> None:
    """State is committed and lives as long as the repo, so it must not grow forever."""
    root = _init_repo(tmp_path, ["alpha", "beta"])
    bad = Patch(files=[File("app/feature.py", "y = 2\n")], summary="add feature")

    for _ in range(2):
        assert _run(monkeypatch, root, bad, guardrail_ok=False, max_attempts=2) == 0
    assert "- [x] alpha" in (root / "BACKLOG.md").read_text(encoding="utf-8")

    good = Patch(files=[File("app/other.py", "z = 3\n")], summary="add other")
    assert _run(monkeypatch, root, good, guardrail_ok=True) == 0

    state = json.loads((root / ".forge" / "state.json").read_text(encoding="utf-8"))
    leftovers = {k: v for k, v in state.items() if k != "__last_failures__"}
    assert leftovers == {}, f"finished tasks left state behind: {leftovers}"
    assert not state.get("__last_failures__")


def _seed_tests(root: Path, count: int) -> str:
    body = "\n".join(f"def test_seed_{i}() -> None:\n    assert True\n" for i in range(count))
    (root / "tests" / "test_seed.py").write_text(body, encoding="utf-8")
    return body


def test_patch_that_shrinks_the_test_suite_is_rejected(tmp_path, monkeypatch) -> None:
    """A green guardrail on a gutted suite must not count as success.

    Patches may write anywhere under tests/, so the cheapest way to "pass" a hard
    task is to delete the tests that make it hard. Lint, import and pytest all stay
    green because they run on whatever is left.
    """
    root = _init_repo(tmp_path, ["do the thing"])
    original = _seed_tests(root, 3)
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "seed tests")

    gutted = Patch(
        files=[File("tests/test_seed.py", "def test_seed_0() -> None:\n    assert True\n")],
        summary="replace the suite",
    )
    monkeypatch.setattr(run, "get_provider", lambda name: _ScriptedProvider(gutted))
    monkeypatch.setattr(run, "run_guardrail", lambda r: GuardrailResult(ok=True, log="stub"))

    rc = run.main(
        ["--repo-root", str(root), "--provider", "scripted", "--no-push", "--max-attempts", "1"]
    )

    assert rc == 0
    assert _is_clean(root)
    assert (root / "tests" / "test_seed.py").read_text(encoding="utf-8") == original
    assert "- [ ] do the thing" not in (root / "BACKLOG.md").read_text(encoding="utf-8")
    assert "shrank" in (root / "DEVLOG.md").read_text(encoding="utf-8")


def test_patch_that_adds_tests_is_accepted(tmp_path, monkeypatch) -> None:
    """The guard must only catch shrinkage — growing the suite is the normal case."""
    root = _init_repo(tmp_path, ["do the thing"])
    _seed_tests(root, 2)
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "seed tests")

    grow = Patch(
        files=[File("tests/test_extra.py", "def test_extra() -> None:\n    assert True\n")],
        summary="add a test",
    )
    monkeypatch.setattr(run, "get_provider", lambda name: _ScriptedProvider(grow))
    monkeypatch.setattr(run, "run_guardrail", lambda r: GuardrailResult(ok=True, log="stub"))

    rc = run.main(
        ["--repo-root", str(root), "--provider", "scripted", "--no-push", "--max-attempts", "1"]
    )

    assert rc == 0
    assert (root / "tests" / "test_extra.py").exists()
    assert "- [x] do the thing" in (root / "BACKLOG.md").read_text(encoding="utf-8")
