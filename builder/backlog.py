"""Reading and updating the markdown backlog.

The backlog is a plain markdown checklist. Each open item is a line beginning
with ``- [ ]``; completed items use ``- [x]``. Keeping it human-readable means
anyone can add, reorder, or rewrite tasks without touching code.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_OPEN = "- [ ] "
_DONE = "- [x] "


@dataclass
class Task:
    """A single backlog item."""

    index: int
    text: str


def next_task(backlog_path: Path) -> Task | None:
    """Return the first open task, or ``None`` when the backlog is exhausted."""
    lines = backlog_path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(_OPEN):
            return Task(index=index, text=stripped[len(_OPEN):].strip())
    return None


def mark_done(backlog_path: Path, index: int, note: str | None = None) -> None:
    """Flip the task at ``index`` from open to done, optionally appending a note."""
    lines = backlog_path.read_text(encoding="utf-8").splitlines()
    line = lines[index]
    prefix, _, rest = line.partition(_OPEN)
    updated = f"{prefix}{_DONE}{rest.strip()}"
    if note:
        updated = f"{updated}  _({note})_"
    lines[index] = updated
    backlog_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
