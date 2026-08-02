"""Self-replenishing backlog generation.

The curated ``BACKLOG.md`` holds over a thousand tasks — roughly a year at three
a day — but a project meant to run for *years* must never simply stop. When the
open backlog runs low, the runtime calls :func:`replenish` to append fresh,
genuinely useful work derived from the toolkit the bot has already built.

The supply is effectively unbounded and, crucially, needs no network or API key:
every public utility the bot ships becomes a source of renewable follow-up work
(more edge-case tests, input validation, worked examples). As the toolkit grows,
so does the pool of future tasks.

That growth argument has a hole in it, though: it only holds while the toolkit is
growing, and a young or stalled toolkit can exhaust the renewable pool. So two
further sources sit underneath it — a catalogue of concrete new utilities, and a
numbered new-module task that is unique by construction. The last one can always
produce work nobody has seen before, which is what actually rules out the two
quiet deaths available to a self-refilling backlog: handing back nothing, or
handing back the same task forever.
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

# Concrete new-utility ideas. These matter more than they look: a renewable task
# only exists because some unit exists, so the pool is themes x units. Shipping a
# *new* unit is therefore the move that grows the pool, and each seed below is a
# real, self-contained piece of work rather than filler.
_SEED_UTILITIES: list[tuple[str, str, str]] = [
    ("strings", "slugify", "turn arbitrary text into a lowercase, hyphen-separated slug"),
    ("strings", "truncate", "shorten text to a maximum length on a word boundary with an ellipsis"),
    ("strings", "strip_html", "remove HTML tags from a string, leaving readable text"),
    ("strings", "title_case", "title-case a sentence while leaving small joining words lowercase"),
    ("collections", "chunk", "split a sequence into consecutive chunks of a given size"),
    ("collections", "flatten", "flatten an arbitrarily nested iterable into a single list"),
    ("collections", "unique", "drop duplicates from an iterable while preserving order"),
    ("collections", "group_by", "group items into a dict keyed by the result of a key function"),
    ("numbers", "clamp", "constrain a number to an inclusive minimum and maximum"),
    ("numbers", "percentage", "compute a percentage safely, returning 0.0 when the total is zero"),
    ("numbers", "human_bytes", "render a byte count as a human-readable size such as 1.2 MB"),
    ("dates", "iso_week", "return the ISO year and week number for a date"),
    ("dates", "humanize_delta", "render a timedelta as a short phrase such as '3 days ago'"),
    ("paths", "safe_filename", "convert a string into a filename safe on every major OS"),
    ("paths", "with_suffix_suffix", "append a suffix to a filename while keeping its extension"),
    ("mapping", "deep_merge", "recursively merge two dictionaries without mutating either"),
    ("mapping", "pluck", "read a nested value from a dict by dotted path with a default"),
    ("text", "word_count", "count words in text, ignoring punctuation and extra whitespace"),
    ("text", "wrap_paragraphs", "re-wrap text to a column width without breaking words"),
    ("validation", "is_valid_email", "check whether a string looks like a valid email address"),
]

_SEED_TEMPLATE = (
    "Add `{name}` to app/toolkit/{module}.py — {description} — with full type hints "
    "and a docstring, export it from app/toolkit/__init__.py, and cover it with "
    "tests in tests/toolkit/test_{module}.py."
)

# Last resort. Numbered so it is unique by construction, which is what guarantees
# replenishment can never degrade into appending one identical task forever. It is
# still real work, and every module it adds multiplies the renewable pool above.
_NEW_MODULE_TEMPLATE = (
    "Add a new well-documented utility module app/toolkit/extra_{n}.py containing at "
    "least one public function with full type hints and a docstring, export it from "
    "app/toolkit/__init__.py, and cover it with tests in tests/toolkit/test_extra_{n}.py."
)


def seed_tasks(existing: set[str], count: int) -> list[str]:
    """Return up to ``count`` new-utility tasks that are not already present."""
    produced: list[str] = []
    for module, name, description in _SEED_UTILITIES:
        if len(produced) >= count:
            break
        task = _SEED_TEMPLATE.format(module=module, name=name, description=description)
        if task not in existing:
            produced.append(task)
    return produced


def novel_module_tasks(existing: set[str], count: int) -> list[str]:
    """Return ``count`` tasks that are guaranteed to be new, however full the backlog."""
    produced: list[str] = []
    n = 1
    while len(produced) < count:
        task = _NEW_MODULE_TEMPLATE.format(n=n)
        if task not in existing:
            produced.append(task)
        n += 1
    return produced


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
    """Return a batch of genuinely new tasks to append.

    Three sources are drawn in order, and every one of them is filtered against the
    tasks already in the backlog: follow-up work on units the bot has built, then
    concrete new utilities, then numbered new modules. The last source can always
    produce something unseen, so this never returns a duplicate and never returns
    nothing — the two ways a self-refilling backlog quietly dies.
    """
    existing = backlog.all_task_texts(backlog_path) if backlog_path.exists() else set()
    units = list_units(repo_root)

    tasks = deterministic_tasks(units, existing, count)
    seen = existing | set(tasks)

    if len(tasks) < count:
        extra = seed_tasks(seen, count - len(tasks))
        tasks.extend(extra)
        seen.update(extra)

    if len(tasks) < count:
        tasks.extend(novel_module_tasks(seen, count - len(tasks)))

    return tasks
