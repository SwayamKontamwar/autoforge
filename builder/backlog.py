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

# Completed items are never deleted, but they cannot stay in one file forever.
# Backlog entries here are full specification lines averaging ~280 bytes and three
# are finished every day, so this is the one part of the file that grows without
# bound; GitHub stops rendering markdown long before it would level off.
#
# The trigger deliberately measures the completed section rather than the whole
# file. Measuring total size would fire on a backlog that is merely long — the
# curated seed is already 288KB of *pending* work — and then archive a handful of
# finished items on every single run, producing a commit and an archive file each
# time while never actually shrinking anything.
MAX_COMPLETED_BYTES = 128 * 1024
_ARCHIVE_DIRNAME = "docs/backlog"


def _archive_dir(backlog_path: Path) -> Path:
    return backlog_path.parent / _ARCHIVE_DIRNAME


def _archive_paths(backlog_path: Path) -> list[Path]:
    directory = _archive_dir(backlog_path)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("completed-*.md"))


def _next_archive_path(backlog_path: Path) -> Path:
    """Return an archive path that does not already exist.

    Numbering off a file *count* looks equivalent but is not: one gap in the sequence
    (``completed-001`` beside ``completed-003``) makes the count point back at a file
    that is already there, and archiving would overwrite it. That destroys finished
    history and shrinks the set of task texts used to reject duplicates, so the bot
    would start regenerating work it had already done.
    """
    directory = _archive_dir(backlog_path)
    directory.mkdir(parents=True, exist_ok=True)
    n = len(_archive_paths(backlog_path)) + 1
    candidate = directory / f"completed-{n:03d}.md"
    while candidate.exists():
        n += 1
        candidate = directory / f"completed-{n:03d}.md"
    return candidate


def archive_completed(backlog_path: Path) -> Path | None:
    """Move finished items into ``docs/backlog/`` once the file grows too large.

    Returns the archive written, or ``None`` when nothing needed moving. Completed
    work stays fully readable and, crucially, still counts for de-duplication —
    forgetting it would let the generator hand back tasks the project already did.
    """
    if not backlog_path.exists():
        return None
    lines = backlog_path.read_text(encoding="utf-8").splitlines()
    done = [line for line in lines if line.strip().startswith(_DONE)]
    if sum(len(line) + 1 for line in done) <= MAX_COMPLETED_BYTES:
        return None
    archive_path = _next_archive_path(backlog_path)
    header = (
        f"# Completed backlog items ({len(done)})\n\n"
        "Moved out of `BACKLOG.md` to keep it readable.\n\n"
    )
    archive_path.write_text(header + "\n".join(done) + "\n", encoding="utf-8")

    rel = f"{_ARCHIVE_DIRNAME}/{archive_path.name}"
    kept = [line for line in lines if not line.strip().startswith(_DONE)]
    note = f"\n_{len(done)} completed items moved to [{rel}]({rel})._\n"
    backlog_path.write_text("\n".join(kept).rstrip("\n") + "\n" + note, encoding="utf-8")
    return archive_path


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
            return Task(index=index, text=stripped[len(_OPEN) :].strip())
    return None


def _relocate(lines: list[str], expect: str | None) -> int:
    """Find the open task whose text is ``expect``, or refuse to guess."""
    if expect is not None:
        wanted = expect.strip()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(_OPEN) and stripped[len(_OPEN) :].strip() == wanted:
                return i
    raise ValueError("backlog index is stale: the file changed after the task was chosen")


def mark_done(
    backlog_path: Path, index: int, note: str | None = None, expect: str | None = None
) -> None:
    """Flip the task at ``index`` from open to done, optionally appending a note.

    ``index`` is read from the file earlier in the run, so it can go stale if anything
    rewrites the backlog in between. Writing to a stale index is worse than failing:
    ``partition`` on a line that is not a task returns the line unchanged, so ``- [x]``
    is welded onto the end of some unrelated line while the real task stays open and is
    handed out again forever. When ``expect`` is given the task is re-located by text,
    and a genuine mismatch raises instead of corrupting the file.
    """
    lines = backlog_path.read_text(encoding="utf-8").splitlines()
    if not 0 <= index < len(lines) or not lines[index].strip().startswith(_OPEN):
        index = _relocate(lines, expect)
    elif expect is not None and lines[index].strip()[len(_OPEN) :].strip() != expect.strip():
        index = _relocate(lines, expect)
    line = lines[index]
    prefix, _, rest = line.partition(_OPEN)
    updated = f"{prefix}{_DONE}{rest.strip()}"
    if note:
        updated = f"{updated}  _({note})_"
    lines[index] = updated
    backlog_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def open_count(backlog_path: Path) -> int:
    """Return how many open (unchecked) tasks remain."""
    lines = backlog_path.read_text(encoding="utf-8").splitlines()
    return sum(1 for line in lines if line.strip().startswith(_OPEN))


def all_task_texts(backlog_path: Path) -> set[str]:
    """Return the text of every task, open or done, for de-duplication.

    Archived items are included. Reading only the live file would make every
    completed task eligible to be generated again the moment it was archived, and
    the project would quietly start rebuilding things it had already built.
    """
    texts: set[str] = set()
    sources = [backlog_path, *_archive_paths(backlog_path)]
    combined = "\n".join(p.read_text(encoding="utf-8") for p in sources if p.exists())
    for line in combined.splitlines():
        stripped = line.strip()
        for marker in (_OPEN, _DONE):
            if stripped.startswith(marker):
                body = stripped[len(marker) :]
                body = body.split("  _(", 1)[0].strip()
                texts.add(body)
                break
    return texts


def append_tasks(backlog_path: Path, tasks: list[str], heading: str) -> None:
    """Append new open tasks under a heading, creating the file if needed."""
    existing = backlog_path.read_text(encoding="utf-8") if backlog_path.exists() else ""
    block = [f"\n## {heading}\n"]
    block.extend(f"- [ ] {task}" for task in tasks)
    body = existing.rstrip("\n") + "\n" + "\n".join(block) + "\n"
    backlog_path.write_text(body, encoding="utf-8")
