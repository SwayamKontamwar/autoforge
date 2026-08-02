"""Regressions for four ways a patch could crash or cheat the loop.

Each was found by review of the crash-safety work and reproduced against the code
as it then stood. Three of them ended the run with an exception after the task had
been chosen but before the attempt was recorded, which is the one failure this
project cannot absorb: the tree stays dirty, the attempt count never rises, and the
same task is chosen and crashes again on every future run.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from builder import run
from builder.guardrail import GuardrailResult
from builder.llm import File, Patch, ProviderError, parse_patch

from .test_run import _init_repo

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_the_no_op_check_runs_before_autofix(tmp_path: Path, monkeypatch) -> None:
    """Ordering, not formatting: autofix rewriting a file must not look like work.

    Asserted against a stand-in for autofix rather than against ruff's real output,
    because which files ruff reformats changes between releases -- and this has to
    keep holding after those releases.
    """
    root = _init_repo(tmp_path, ["t"])
    target = root / "app" / "main.py"
    verbatim = target.read_text(encoding="utf-8")

    def _reformats(repo_root: Path, patch: Patch) -> None:
        target.write_text(verbatim + "# reformatted\n", encoding="utf-8")

    monkeypatch.setattr(run, "_autofix", _reformats)
    monkeypatch.setattr(run, "run_guardrail", lambda r: GuardrailResult(ok=True, log="stub"))

    result = run._judge(root, Patch(files=[File("app/main.py", verbatim)], summary="no-op"))

    assert result.ok is False
    assert "unchanged" in result.log


def test_autofix_still_runs_for_a_real_patch(tmp_path: Path, monkeypatch) -> None:
    """Moving the check earlier must not skip autofix for genuine work."""
    root = _init_repo(tmp_path, ["t"])
    called: list[str] = []
    monkeypatch.setattr(run, "_autofix", lambda r, p: called.append("yes"))
    monkeypatch.setattr(run, "run_guardrail", lambda r: GuardrailResult(ok=True, log="stub"))

    result = run._judge(root, Patch(files=[File("app/new.py", "z = 3\n")], summary="s"))

    assert result.ok is True
    assert called == ["yes"]


@pytest.mark.parametrize("path", ["app/router.py/user.py", "tests/test_a.py/helper.py"])
def test_a_path_nested_inside_a_module_file_is_rejected(path: str) -> None:
    """Such a path creates a *directory* named "*.py" that later crashes prompt building."""
    assert run._reject_reason(Patch(files=[File(path, "x = 1\n")], summary="s")) is not None


def test_an_ordinary_module_path_is_still_allowed() -> None:
    assert run._reject_reason(Patch(files=[File("app/router.py", "x = 1\n")], summary="s")) is None


def test_building_context_survives_a_directory_named_like_a_module(tmp_path: Path) -> None:
    (tmp_path / "app" / "router.py").mkdir(parents=True)
    (tmp_path / "app" / "router.py" / "user.py").write_text("x = 1\n", encoding="utf-8")

    run._build_context(tmp_path, "Add a User router in app/router.py")


@pytest.mark.parametrize(
    "payload",
    [
        '[{"path": "app/a.py", "content": "x = 1"}]',  # a bare array of files
        '{"files": ["app/a.py"], "summary": "s"}',  # files as plain strings
        '"just a string"',
        "42",
    ],
)
def test_json_of_the_wrong_shape_is_a_provider_error(payload: str) -> None:
    with pytest.raises(ProviderError):
        parse_patch(payload)


def test_a_well_formed_patch_still_parses() -> None:
    patch = parse_patch('{"files": [{"path": "app/a.py", "content": "x = 1\\n"}], "summary": "s"}')

    assert patch.files[0].path == "app/a.py"


def test_ignore_rules_do_not_hide_work_inside_app_or_tests(tmp_path: Path) -> None:
    """Unanchored build/ and dist/ patterns would match at any depth.

    A patch landing there is real work, but git would not report it, so the no-op
    check would reject it and the task would be skipped after three good attempts.
    """
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_text(
        (_REPO_ROOT / ".gitignore").read_text(encoding="utf-8"), encoding="utf-8"
    )
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)

    candidates = ("app/build/x.py", "app/dist/y.py", "tests/build/z.py", "app/pkg.egg-info/a.py")
    for candidate in candidates:
        ignored = (
            subprocess.run(
                ["git", "check-ignore", "-q", candidate], cwd=root, capture_output=True
            ).returncode
            == 0
        )
        assert not ignored, f"{candidate} is hidden from git status"


def test_root_build_artefacts_are_still_ignored(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".gitignore").write_text(
        (_REPO_ROOT / ".gitignore").read_text(encoding="utf-8"), encoding="utf-8"
    )
    subprocess.run(["git", "init", "-q"], cwd=root, check=True, capture_output=True)

    candidates = ("build/x.py", "dist/y.py", "autoforge.egg-info/a.py", "app/__pycache__/m.pyc")
    for candidate in candidates:
        ignored = (
            subprocess.run(
                ["git", "check-ignore", "-q", candidate], cwd=root, capture_output=True
            ).returncode
            == 0
        )
        assert ignored, f"{candidate} should still be ignored"
