"""Regression tests for the incident where a green run was wrong.

Asked to add ``GET /stats``, the bot shipped no endpoint and no test -- only a
monkey-patch of ``TestClient`` inside ``app/__init__.py`` so its earlier mistake
would be accepted. Lint, import and pytest all passed, and the task was ticked
off. These tests hold that door shut.

Each test below fails against the code as it was before ``builder/honesty.py``.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

from builder import honesty
from builder import run as run
from builder.llm import _SYSTEM_PROMPT, _TESTCLIENT_REDIRECT_HINT, File, Patch
from builder.run import _reject_reason

REPO_ROOT = Path(__file__).resolve().parents[1]

# The real payload from commit c12f943, reduced to the part that did the damage.
REAL_MONKEYPATCH = '''"""URL-shortener API."""

from fastapi.testclient import TestClient as _FastAPITestClient


def _wrap(method):
    def inner(self, *args, allow_redirects=None, **kwargs):
        if allow_redirects is not None:
            kwargs["follow_redirects"] = allow_redirects
        return method(self, *args, **kwargs)

    return inner


_FastAPITestClient.get = _wrap(_FastAPITestClient.get)
_FastAPITestClient.post = _wrap(_FastAPITestClient.post)
'''


def _patch(*pairs: tuple[str, str]) -> Patch:
    return Patch(
        summary="add a feature",
        files=[File(path=path, content=content) for path, content in pairs],
    )


class TestRejectsTheRealIncident:
    def test_the_exact_committed_payload_is_rejected(self):
        reason = _reject_reason(_patch(("app/__init__.py", REAL_MONKEYPATCH)))
        assert reason is not None
        assert "app/__init__.py" in reason

    def test_rejection_names_the_harness_import(self):
        reason = honesty.rigged_verdict_reason(
            [File(path="app/__init__.py", content=REAL_MONKEYPATCH)]
        )
        assert "testclient" in reason.lower()

    def test_alias_does_not_evade_the_reassignment_check(self):
        """The real commit renamed the import, which a name-match alone would miss."""
        tree = ast.parse(REAL_MONKEYPATCH)
        assert honesty._patches_harness(tree) is not None

    def test_repo_no_longer_contains_the_monkeypatch(self):
        source = (REPO_ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
        assert "TestClient" not in source
        assert "allow_redirects" not in source


class TestProductionMustNotImportTheHarness:
    @pytest.mark.parametrize(
        "statement",
        [
            "import pytest",
            "import unittest",
            "from pytest import fixture",
            "from unittest import mock",
            "from fastapi.testclient import TestClient",
            "from starlette.testclient import TestClient",
            "import fastapi.testclient",
            "from _pytest.config import Config",
        ],
    )
    def test_rejected_in_app(self, statement):
        assert _reject_reason(_patch(("app/thing.py", f"{statement}\n"))) is not None

    @pytest.mark.parametrize(
        "statement",
        [
            "import pytest",
            "from fastapi.testclient import TestClient",
        ],
    )
    def test_allowed_in_tests(self, statement):
        """Tests are supposed to import testing tools; only app/ is constrained."""
        assert _reject_reason(_patch(("tests/test_x.py", f"{statement}\n"))) is None

    def test_ordinary_production_imports_still_pass(self):
        content = (
            "import json\n"
            "from dataclasses import dataclass\n"
            "from fastapi import FastAPI\n"
            "from app.main import app\n"
        )
        assert _reject_reason(_patch(("app/thing.py", content))) is None

    def test_a_name_merely_containing_pytest_is_not_flagged(self):
        assert _reject_reason(_patch(("app/x.py", "import pytestish\n"))) is None


class TestHarnessReassignment:
    def test_rejected_even_from_tests(self):
        """Rewriting the harness is out of bounds wherever it happens."""
        content = "from fastapi.testclient import TestClient\nTestClient.get = None\n"
        assert _reject_reason(_patch(("tests/test_x.py", content))) is not None

    def test_assigning_to_own_object_is_fine(self):
        content = "class Thing:\n    pass\n\nthing = Thing()\nthing.get = 1\n"
        assert _reject_reason(_patch(("app/x.py", content))) is None


class TestSuiteMustGrow:
    """The old rule only caught a *shrinking* suite, so zero new tests passed."""

    def test_production_change_with_no_new_tests_is_rejected(self):
        reason = honesty.untested_production_reason(
            [File(path="app/main.py", content="x = 1\n")],
            tests_before=200,
            tests_after=200,
        )
        assert reason is not None and "200" in reason

    def test_production_change_with_a_new_test_passes(self):
        assert (
            honesty.untested_production_reason(
                [File(path="app/main.py", content="x = 1\n")],
                tests_before=200,
                tests_after=201,
            )
            is None
        )

    def test_tests_only_patch_is_not_required_to_grow(self):
        """Some tasks legitimately rewrite a test without adding one."""
        assert (
            honesty.untested_production_reason(
                [File(path="tests/test_x.py", content="x = 1\n")],
                tests_before=200,
                tests_after=200,
            )
            is None
        )

    @pytest.mark.parametrize(
        ("before", "after"),
        [(-1, 200), (200, -1), (-1, -1)],
    )
    def test_unmeasurable_counts_do_not_reject(self, before, after):
        """-1 means pytest could not be collected: unknown, not zero."""
        assert (
            honesty.untested_production_reason(
                [File(path="app/main.py", content="x = 1\n")], before, after
            )
            is None
        )


class TestPromptTellsTheTruth:
    def test_hint_matches_the_installed_client(self):
        """If a dependency bump changes this, the hint must be corrected, not left lying."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        with pytest.raises(TypeError):
            client.get("/healthz", allow_redirects=False)
        assert client.get("/healthz", follow_redirects=False).status_code == 200

    def test_hint_is_actually_in_the_prompt(self):
        assert _TESTCLIENT_REDIRECT_HINT in _SYSTEM_PROMPT
        assert "follow_redirects" in _SYSTEM_PROMPT

    def test_prompt_forbids_patching_the_harness(self):
        lowered = _SYSTEM_PROMPT.lower()
        assert "never import pytest" in lowered
        assert "reassign" in lowered


class TestGuardrailIntegration:
    def test_a_rigged_patch_is_refused_end_to_end(self, tmp_path):
        """The check is reachable from the entry point, not just unit-testable."""
        script = (
            "import sys; sys.path.insert(0, %r)\n"
            "from builder.run import _reject_reason\n"
            "from builder.llm import File, Patch\n"
            "p = Patch(summary='s', files=[File(path='app/__init__.py', content=%r)])\n"
            "r = _reject_reason(p)\n"
            "sys.exit(0 if r else 1)\n"
        ) % (str(REPO_ROOT), REAL_MONKEYPATCH)
        proc = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, cwd=tmp_path
        )
        assert proc.returncode == 0, proc.stderr.decode()

    def test_reopened_stats_task_is_open(self):
        """It was ticked off with nothing built; it must be available again."""
        backlog = (REPO_ROOT / "BACKLOG.md").read_text(encoding="utf-8")
        line = next(ln for ln in backlog.splitlines() if "GET /stats returning totals" in ln)
        assert line.startswith("- [ ]")


class TestHostileModelOutput:
    """The check parses untrusted model output; it must never be the thing that crashes.

    ``lone surrogate`` is not theoretical -- it is what a mangled UTF-8 response
    decodes to, and it raised UnicodeEncodeError out of ``ast.parse`` until this
    was widened.
    """

    @pytest.mark.parametrize(
        ("name", "content"),
        [
            ("null byte", "x = 1\x00\n"),
            ("lone surrogate", "x = 1\n\udcff"),
            ("deep nesting", "x = " + "(" * 200 + "1" + ")" * 200 + "\n"),
            ("very deep nesting", "x = " + "[" * 10000 + "]" * 10000 + "\n"),
            ("syntax error", "def (:\n"),
            ("empty", ""),
            ("bom only", "\ufeff"),
            ("huge string", "x = '" + "a" * 200000 + "'\n"),
        ],
    )
    def test_does_not_raise(self, name, content):
        assert _reject_reason(_patch((f"app/{name.replace(' ', '_')}.py", content))) is None

    def test_non_python_files_are_not_parsed(self):
        assert _reject_reason(_patch(("app/data.txt", "\x00\udcff not python"))) is None


class TestRetiredKwargIsRepaired:
    """The prompt hint was not enough -- the model wrote the dead keyword anyway.

    Live evidence: with the correct name stated in the prompt AND the previous
    ``TypeError`` fed back as retry feedback, the very next run still emitted
    ``allow_redirects=``. Asking does not work, so it is rewritten mechanically.
    """

    def test_the_swap_matches_the_installed_client(self):
        from builder.run import _retired_kwarg_rewrite

        assert _retired_kwarg_rewrite() == ("allow_redirects", "follow_redirects")

    def test_rewrites_the_real_failing_line(self, tmp_path):
        from builder.run import _fix_retired_kwargs

        (tmp_path / "tests").mkdir()
        body = 'r = client.get("/abc", allow_redirects=False)\n'
        (tmp_path / "tests" / "test_stats.py").write_text(body)
        patch = _patch(("tests/test_stats.py", body))
        assert _fix_retired_kwargs(tmp_path, patch) == ["tests/test_stats.py"]
        fixed = (tmp_path / "tests" / "test_stats.py").read_text()
        assert "follow_redirects=False" in fixed
        assert "allow_redirects" not in fixed

    def test_rewritten_call_actually_works(self):
        """The replacement must be accepted by the real client, not merely different."""
        from fastapi.testclient import TestClient

        from app.main import app

        assert TestClient(app).get("/healthz", follow_redirects=False).status_code == 200

    def test_production_files_are_never_rewritten(self, tmp_path):
        from builder.run import _fix_retired_kwargs

        (tmp_path / "app").mkdir()
        body = "allow_redirects = True\n"
        (tmp_path / "app" / "x.py").write_text(body)
        assert _fix_retired_kwargs(tmp_path, _patch(("app/x.py", body))) == []
        assert (tmp_path / "app" / "x.py").read_text() == body

    def test_unrelated_code_is_untouched(self, tmp_path):
        from builder.run import _fix_retired_kwargs

        (tmp_path / "tests").mkdir()
        body = "x = disallow_redirects_thing\n"
        (tmp_path / "tests" / "test_a.py").write_text(body)
        assert _fix_retired_kwargs(tmp_path, _patch(("tests/test_a.py", body))) == []

    def test_missing_file_does_not_raise(self, tmp_path):
        from builder.run import _fix_retired_kwargs

        assert _fix_retired_kwargs(tmp_path, _patch(("tests/gone.py", "x = 1\n"))) == []


class TestRetirementIsProvisional:
    """A task retired by a builder bug was never evidence about the task.

    Two real tasks here were retired solely because the model kept writing a
    keyword the installed httpx had removed. Both were solvable throughout. At the
    observed rate -- 2 of 12 attempted -- that is a sixth of a 2,000-task backlog
    quietly abandoned over the years this is meant to run.
    """

    def test_fingerprint_tracks_builder_changes_only(self, tmp_path):
        from builder.run import _builder_fingerprint

        (tmp_path / "builder").mkdir()
        (tmp_path / "builder" / "run.py").write_text("x = 1\n")
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "main.py").write_text("y = 1\n")
        first = _builder_fingerprint(tmp_path)
        assert first

        # The product changing every run must not count as the builder changing,
        # or the skip threshold would reset constantly and mean nothing.
        (tmp_path / "app" / "main.py").write_text("y = 99999\n")
        assert _builder_fingerprint(tmp_path) == first

        (tmp_path / "builder" / "run.py").write_text("x = 2\n")
        assert _builder_fingerprint(tmp_path) != first

    def test_no_builder_means_no_fingerprint(self, tmp_path):
        """The empty hash is a stable value and must not pass as a real one."""
        from builder.run import _builder_fingerprint

        assert _builder_fingerprint(tmp_path) == ""

    def test_revive_reopens_and_strips_the_note(self, tmp_path):
        from builder import backlog

        p = tmp_path / "BACKLOG.md"
        p.write_text(
            "# B\n\n"
            "- [ ] still open\n"
            "- [x] genuinely done\n"
            "- [x] was retired  _(skipped after 3 failed attempts)_\n"
        )
        assert backlog.revive_skipped(p) == ["was retired"]
        text = p.read_text()
        assert "- [ ] was retired\n" in text
        assert "skipped after" not in text
        assert "- [x] genuinely done" in text, "real completions must not be reopened"

    def test_revive_is_capped(self, tmp_path):
        """One builder change must not re-grind an unbounded pile of dead work."""
        from builder import backlog

        p = tmp_path / "BACKLOG.md"
        p.write_text(
            "# B\n\n"
            + "".join(
                f"- [x] task {i}  _(skipped after 3 failed attempts)_\n" for i in range(200)
            )
        )
        revived = backlog.revive_skipped(p)
        assert len(revived) == backlog.REVIVE_LIMIT

    def test_nothing_to_revive_leaves_the_file_alone(self, tmp_path):
        from builder import backlog

        p = tmp_path / "BACKLOG.md"
        body = "# B\n\n- [ ] open\n- [x] done\n"
        p.write_text(body)
        assert backlog.revive_skipped(p) == []
        assert p.read_text() == body

    def test_refresh_only_fires_when_the_builder_changes(self, tmp_path):
        from builder.run import _BUILDER_KEY, _FAILURES_KEY, _refresh_stale_evidence

        (tmp_path / "builder").mkdir()
        (tmp_path / "builder" / "run.py").write_text("x = 1\n")
        p = tmp_path / "BACKLOG.md"
        p.write_text("# B\n\n- [x] dead  _(skipped after 3 failed attempts)_\n")

        # First ever run: nothing is known yet, so nothing is stale.
        state = {"some task": 2, _FAILURES_KEY: {"some task": "log"}}
        assert _refresh_stale_evidence(tmp_path, p, state) == []
        assert state["some task"] == 2
        assert state[_BUILDER_KEY]

        # Unchanged builder: the counts still mean what they said.
        assert _refresh_stale_evidence(tmp_path, p, state) == []
        assert state["some task"] == 2

        (tmp_path / "builder" / "run.py").write_text("x = 2\n")
        assert _refresh_stale_evidence(tmp_path, p, state) == ["dead"]
        assert "some task" not in state, "stale attempt counts must be cleared"
        assert state[_FAILURES_KEY] == {}

    def test_fingerprint_survives_state_sanitising(self, tmp_path):
        """The state file is committed and sanitised on load; a dropped key = no-op."""
        from builder.run import _BUILDER_KEY, _load_state, _save_state

        p = tmp_path / "state.json"
        _save_state(p, {_BUILDER_KEY: "abc123"})
        assert _load_state(p).get(_BUILDER_KEY) == "abc123"

    def test_the_two_bug_retired_tasks_are_no_longer_retired(self):
        """Neither task may sit in the retired state again.

        This deliberately does not assert they are *open*. An earlier version did,
        and it broke the moment the system worked -- the bot picked up the revived
        alias task and genuinely completed it, so the line correctly reads ``- [x]``
        with no skip note. Asserting a transient state punishes success. What must
        stay true is that neither was abandoned by a builder bug.
        """
        text = (REPO_ROOT / "BACKLOG.md").read_text(encoding="utf-8")
        for want in ("GET /stats returning totals", "Support a custom alias on POST /links"):
            line = next(ln for ln in text.splitlines() if want in ln)
            assert "skipped after" not in line, line


class TestUndecodableFilesRefuseInsteadOfCrashing:
    """Found by soaking: one invalid byte wedged the loop permanently.

    BACKLOG.md and DEVLOG.md are read as UTF-8 by six different functions. A
    single invalid byte raised UnicodeDecodeError from whichever ran first, as a
    bare traceback. Both files are committed, so the same bytes return on every
    future checkout and the run dies in exactly the same place forever.
    """

    @pytest.mark.parametrize("name", ["BACKLOG.md", "DEVLOG.md"])
    def test_layout_guard_names_the_bad_file(self, tmp_path, name):
        from builder.run import _unusable_layout

        backlog = tmp_path / "BACKLOG.md"
        devlog = tmp_path / "DEVLOG.md"
        backlog.write_text("# B\n\n- [ ] a task\n", encoding="utf-8")
        devlog.write_text("# D\n", encoding="utf-8")
        (tmp_path / name).write_bytes(b"\x00\xff\xfe not utf-8 \x00")

        reason = _unusable_layout(tmp_path, backlog, devlog)
        assert name in reason
        assert "UTF-8" in reason

    def test_valid_files_are_accepted(self, tmp_path):
        from builder.run import _unusable_layout

        backlog = tmp_path / "BACKLOG.md"
        devlog = tmp_path / "DEVLOG.md"
        backlog.write_text("# B\n\n- [ ] a task with unicode: caf\u00e9 \u4e2d\u6587\n")
        devlog.write_text("# D\n\u2014 dash\n")
        assert _unusable_layout(tmp_path, backlog, devlog) == ""

    def test_missing_devlog_is_not_an_error(self, tmp_path):
        """DEVLOG.md is created on first write; absent is normal, not broken."""
        from builder.run import _unusable_layout

        backlog = tmp_path / "BACKLOG.md"
        backlog.write_text("# B\n\n- [ ] a task\n")
        assert _unusable_layout(tmp_path, backlog, tmp_path / "DEVLOG.md") == ""

    def test_corrupt_archive_does_not_crash_task_lookup(self, tmp_path):
        """Archives are not covered by the layout guard, so they must be tolerant."""
        from builder import backlog

        p = tmp_path / "BACKLOG.md"
        p.write_text("# B\n\n- [ ] live task\n", encoding="utf-8")
        archive = tmp_path / "docs" / "backlog"
        archive.mkdir(parents=True)
        (archive / "completed-001.md").write_bytes(b"- [x] old task\n\xff\xfe\x00")

        texts = backlog.all_task_texts(p)
        assert "live task" in texts
        assert "old task" in texts


class TestUnwritableFilesRefuseInsteadOfCrashing:
    """Found by soaking: an unwritable file crashed after the work was already done.

    Every run appends to DEVLOG.md and rewrites BACKLOG.md. When either could not
    be written the run raised a bare PermissionError -- and it raised it *after*
    calling the model and running the guardrail, so the work was thrown away with
    no explanation. A full disk on a machine running for years produces the same
    class of error.
    """

    @pytest.fixture
    def repo(self, tmp_path):
        backlog = tmp_path / "BACKLOG.md"
        devlog = tmp_path / "DEVLOG.md"
        backlog.write_text("# B\n\n- [ ] a task\n", encoding="utf-8")
        devlog.write_text("# D\n", encoding="utf-8")
        return tmp_path, backlog, devlog

    @pytest.mark.parametrize("name", ["BACKLOG.md", "DEVLOG.md"])
    def test_unwritable_file_is_named(self, repo, name):
        from builder.run import _unusable_layout

        root, backlog, devlog = repo
        target = root / name
        target.chmod(0o444)
        try:
            reason = _unusable_layout(root, backlog, devlog)
        finally:
            target.chmod(0o644)
        assert name in reason
        assert "writable" in reason

    def test_unwritable_repo_root_is_named(self, repo):
        from builder.run import _unusable_layout

        root, backlog, devlog = repo
        root.chmod(0o555)
        try:
            reason = _unusable_layout(root, backlog, devlog)
        finally:
            root.chmod(0o755)
        assert "writable" in reason

    def test_writable_repo_is_accepted(self, repo):
        from builder.run import _unusable_layout

        root, backlog, devlog = repo
        assert _unusable_layout(root, backlog, devlog) == ""

    def test_probe_leaves_nothing_behind(self, repo):
        """A probe file is one SIGKILL away from being swept into a commit."""
        from builder.run import _unusable_layout

        root, backlog, devlog = repo
        before = {p.name for p in root.iterdir()}
        assert _unusable_layout(root, backlog, devlog) == ""
        assert {p.name for p in root.iterdir()} == before

    def test_probe_does_not_alter_contents(self, repo):
        """Opening for append must not truncate or modify the files it checks."""
        from builder.run import _unusable_layout

        root, backlog, devlog = repo
        before = (backlog.read_text(), devlog.read_text())
        assert _unusable_layout(root, backlog, devlog) == ""
        assert (backlog.read_text(), devlog.read_text()) == before


class TestAmbiguousLambdaParamIsRenamed:
    """E741 caused a third of all guardrail failures: real code, thrown away over
    the name of a throwaway variable. ruff cannot fix it, so the builder does."""

    def test_the_real_rejected_line_is_repaired(self):
        source = "most_visited = max(links, key=lambda l: l.hits)\n"
        assert run._rename_ambiguous_lambda_params(source) == (
            "most_visited = max(links, key=lambda item: item.hits)\n"
        )

    def test_capital_i_and_o_are_renamed_too(self):
        out = run._rename_ambiguous_lambda_params("f = lambda I: I.x\n")
        assert out is not None and "lambda I:" not in out

    def test_a_body_that_rebinds_the_name_is_left_alone(self):
        # Here the `l` in the body is the comprehension's, not the parameter's.
        source = "f = lambda l: [l for l in range(l)]\n"
        assert run._rename_ambiguous_lambda_params(source) is None

    def test_an_outer_scope_use_is_never_touched(self):
        out = run._rename_ambiguous_lambda_params("l = 5\nf = lambda l: l.x\nprint(l)\n")
        assert out is not None
        assert "l = 5" in out and "print(l)" in out

    def test_module_level_assignment_is_not_renamed(self):
        # Only lambda parameters are provably safe to rename; bindings that leak
        # into surrounding scope are deliberately left for the model to fix.
        assert run._rename_ambiguous_lambda_params("l = compute()\nuse(l)\n") is None

    def test_a_collision_with_an_existing_name_is_avoided(self):
        out = run._rename_ambiguous_lambda_params("item = 1\nf = lambda l: l + item\n")
        assert out is not None and "lambda item:" not in out

    @pytest.mark.parametrize(
        ("source", "call"),
        [
            ("f = lambda l: l * 2", "f(21)"),
            ("f = lambda l: (lambda l: l + 1)(l * 10)", "f(3)"),
            ("f = lambda l: (lambda z: z + l)", "f(10)(5)"),
            ("f = lambda l: (n := l + 1) + n", "f(5)"),
            ("f = lambda *l: sum(l)", "f(1, 2, 3)"),
            ("l = 100\nf = lambda l: l + 1", "(f(1), l)"),
            ("f = lambda I, O: I - O", "f(10, 4)"),
        ],
    )
    def test_the_rename_never_changes_behaviour(self, source, call):
        rewritten = run._rename_ambiguous_lambda_params(source) or source
        before, after = {}, {}
        exec(source, before)  # noqa: S102
        exec(rewritten, after)  # noqa: S102
        assert eval(call, before) == eval(call, after)  # noqa: S307

    @pytest.mark.parametrize(
        "source",
        [
            "def (\n",
            "lambda l: \ud800",
            "\x00lambda l: l",
            "f = " + "lambda l: " * 2000 + "l",  # blows the stack in ast.dump
        ],
    )
    def test_hostile_input_is_declined_not_raised(self, source):
        assert run._rename_ambiguous_lambda_params(source) is None

    def test_autofix_repairs_a_generated_file(self, tmp_path):
        (tmp_path / "app").mkdir()
        target = tmp_path / "app" / "main.py"
        target.write_text("best = max(rows, key=lambda l: l.hits)\n", encoding="utf-8")
        patch = Patch(
            files=[File(path="app/main.py", content=target.read_text(encoding="utf-8"))],
            summary="m",
        )
        assert run._fix_ambiguous_names(tmp_path, patch) == ["app/main.py"]
        assert "lambda l:" not in target.read_text(encoding="utf-8")
