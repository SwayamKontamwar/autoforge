"""The correctness guardrail: lint, tests, and an import smoke check.

Generated code is committed only if every check here passes. This is the single
promise the experiment makes about its own history: it may contain imperfect
design, but it never contains a state that fails to lint, import, or test.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GuardrailResult:
    """Outcome of running the guardrail."""

    ok: bool
    log: str


def _run(label: str, args: list[str], cwd: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=600,
    )
    ok = proc.returncode == 0
    output = (proc.stdout + proc.stderr).strip()
    return ok, f"$ {label}\n(exit {proc.returncode})\n{output}\n"


def run(repo_root: Path) -> GuardrailResult:
    """Run ruff, an import check, and pytest. Stop at the first failure."""
    checks: list[tuple[str, list[str]]] = [
        ("ruff check", [sys.executable, "-m", "ruff", "check", "."]),
        ("import app.main", [sys.executable, "-c", "import app.main"]),
        ("pytest", [sys.executable, "-m", "pytest"]),
    ]
    log = ""
    for label, args in checks:
        ok, section = _run(label, args, repo_root)
        log += section
        if not ok:
            return GuardrailResult(ok=False, log=log)
    return GuardrailResult(ok=True, log=log)
