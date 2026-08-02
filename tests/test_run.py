"""Orchestrator autonomy tests.

These exercise ``builder.run.main`` end to end against a real temporary git repo,
with the model provider and the guardrail stubbed so the test is fast and
hermetic. They lock down the promises the unattended loop must keep: it never
leaves a dirty tree, it advances or safely skips every task, and it records
honest state for each outcome.
"""

from __future__ import annotations

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
    monkeypatch.setattr(
        run, "run_guardrail", lambda repo_root: GuardrailResult(ok=guardrail_ok, log="stub")
    )
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
