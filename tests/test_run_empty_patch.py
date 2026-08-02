"""A task may only be ticked off by work that actually exists.

The failure this guards against is the quiet kind: the run reports success, the
backlog item is marked done, the devlog records a completed task -- and not one
line of code was written. Over a long run that silently eats the backlog while
every signal says the project is healthy.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from builder import run
from builder.guardrail import GuardrailResult
from builder.llm import File, Patch

from .test_run import _init_repo, _is_clean, _ScriptedProvider


def test_a_patch_with_no_files_is_rejected() -> None:
    assert run._reject_reason(Patch(files=[], summary="nothing")) is not None


def test_a_patch_with_files_is_still_accepted() -> None:
    patch = Patch(files=[File("app/thing.py", "x = 1\n")], summary="s")

    assert run._reject_reason(patch) is None


def test_an_empty_patch_does_not_complete_the_task(tmp_path: Path, monkeypatch) -> None:
    root = _init_repo(tmp_path, ["do the thing"])
    empty = Patch(files=[], summary="n")
    monkeypatch.setattr(run, "get_provider", lambda name: _ScriptedProvider(empty))
    monkeypatch.setattr(run, "run_guardrail", lambda r: GuardrailResult(ok=True, log="stub"))

    rc = run.main(["--repo-root", str(root), "--provider", "scripted", "--no-push"])

    assert rc == 0
    assert _is_clean(root)
    assert "- [ ] do the thing" in (root / "BACKLOG.md").read_text(encoding="utf-8")


def test_a_patch_that_changes_nothing_is_not_a_success(tmp_path: Path, monkeypatch) -> None:
    """A model can return an existing file verbatim; the guardrail would pass on it."""
    root = _init_repo(tmp_path, ["do the thing"])
    existing = root / "app" / "main.py"
    patch = Patch(
        files=[File("app/main.py", existing.read_text(encoding="utf-8"))], summary="no-op"
    )
    monkeypatch.setattr(run, "get_provider", lambda name: _ScriptedProvider(patch))
    monkeypatch.setattr(run, "run_guardrail", lambda r: GuardrailResult(ok=True, log="stub"))

    rc = run.main(["--repo-root", str(root), "--provider", "scripted", "--no-push"])

    assert rc == 0
    assert _is_clean(root)
    assert "- [ ] do the thing" in (root / "BACKLOG.md").read_text(encoding="utf-8")
    state = run._load_state(root / ".forge" / "state.json")
    assert state.get("do the thing") == 1


def test_the_no_op_log_tells_the_model_what_happened(tmp_path: Path, monkeypatch) -> None:
    root = _init_repo(tmp_path, ["t"])
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    existing = (root / "app" / "main.py").read_text(encoding="utf-8")
    patch = Patch(files=[File("app/main.py", existing)], summary="no-op")

    result = run._judge(root, patch)

    assert result.ok is False
    assert "unchanged" in result.log


def test_a_real_change_still_reaches_the_guardrail(tmp_path: Path, monkeypatch) -> None:
    """The no-op check must not swallow genuine work."""
    root = _init_repo(tmp_path, ["t"])
    monkeypatch.setattr(run, "run_guardrail", lambda r: GuardrailResult(ok=True, log="real"))

    result = run._judge(root, Patch(files=[File("app/new.py", "z = 3\n")], summary="s"))

    assert result.ok is True
    assert result.log == "real"
