"""Self-replenishing backlog generation.

The curated ``BACKLOG.md`` holds over a thousand tasks — roughly a year at three
a day — but a project meant to run for *years* must never simply stop. When the
open backlog runs low, the runtime calls :func:`replenish` to append fresh,
genuinely useful work derived from the toolkit the bot has already built.

The supply is effectively unbounded and, crucially, needs no network or API key:
every public utility the bot ships becomes a source of renewable follow-up work
(more edge-case tests, input validation, worked examples). As the toolkit grows,
so does the pool of future tasks. This is what turns "a big list" into "runs for
years."
"""

from __future__ import annotations

import ast
from pathlib import Path

from builder import backlog

# Templates take a module and a unit (function/class) name and produce one task.
# They are deliberately safe: each edits allowed paths and yields a real diff the
# guardrail can verify, and none depend on the network or optional tooling.
_RENEWABLE_THEMES: list[str] = [
    "Add further edge-case tests for `{name}` in tests/toolkit/test_{module}.py "
    "covering empty, boundary, and unusually large inputs.",
    "Add explicit input validation to `{name}` in app/toolkit/{module}.py, raising "
    "a clear ValueError on invalid arguments, and cover it with a test.",
    "Add a worked example to the docstring of `{name}` in app/toolkit/{module}.py "
    "and assert that example in tests/toolkit/test_{module}.py.",
]

_FALLBACK_TASK = (
    "Add a new small, well-documented utility to app/toolkit/strings.py with full "
    "type hints, export it from app/toolkit/__init__.py, and cover it with a pytest."
)


def _toolkit_dir(repo_root: Path) -> Path:
    return repo_root / "app" / "toolkit"


def list_units(repo_root: Path) -> list[tuple[str, str]]:
    """Return ``(module, name)`` for every public function/class in the toolkit."""
    toolkit = _toolkit_dir(repo_root)
    units: list[tuple[str, str]] = []
    if not toolkit.is_dir():
        return units
    for path in sorted(toolkit.glob("*.py")):
        if path.name == "__init__.py":
            continue
        module = path.stem
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    units.append((module, node.name))
    return units


def deterministic_tasks(
    units: list[tuple[str, str]], existing: set[str], count: int
) -> list[str]:
    """Produce up to ``count`` renewable tasks not already present in ``existing``."""
    produced: list[str] = []
    seen = set(existing)
    for theme in _RENEWABLE_THEMES:
        for module, name in units:
            if len(produced) >= count:
                return produced
            task = theme.format(module=module, name=name)
            if task not in seen:
                seen.add(task)
                produced.append(task)
    return produced


def replenish(repo_root: Path, backlog_path: Path, count: int) -> list[str]:
    """Return a batch of new tasks to append, guaranteed non-empty."""
    existing = backlog.all_task_texts(backlog_path) if backlog_path.exists() else set()
    units = list_units(repo_root)
    tasks = deterministic_tasks(units, existing, count)
    if not tasks:
        tasks = [_FALLBACK_TASK]
    return tasks
