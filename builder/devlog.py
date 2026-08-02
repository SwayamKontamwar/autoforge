"""Appending dated entries to the development log.

Every run — success or failure — leaves an honest, timestamped record so the
git history reads like a real engineering journal rather than opaque bot noise.

At three entries a day the log outgrows what GitHub will render in about a year
and a half, at which point the web UI replaces the project's most readable
artefact with "we can't show files that are this big". So the log rotates: once
it passes the threshold the current file is archived under ``docs/devlog/`` and a
fresh one starts, with a link back. Nothing is ever deleted.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

# GitHub stops rendering markdown at around 1 MB. Rotate well before that so the
# live log always opens, and an archive is never a borderline case either.
MAX_DEVLOG_BYTES = 512 * 1024

_ARCHIVE_DIR = Path("docs") / "devlog"


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def _archive_dir(devlog_path: Path) -> Path:
    return devlog_path.parent / _ARCHIVE_DIR


def _next_archive_path(devlog_path: Path) -> Path:
    archive = _archive_dir(devlog_path)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m")
    candidate = archive / f"devlog-{stamp}.md"
    n = 2
    while candidate.exists():
        candidate = archive / f"devlog-{stamp}-{n}.md"
        n += 1
    return candidate


def _rotate(devlog_path: Path) -> Path:
    """Move the current log into the archive and start a fresh one linking to it."""
    archive_path = _next_archive_path(devlog_path)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_text(devlog_path.read_text(encoding="utf-8"), encoding="utf-8")
    rel = archive_path.relative_to(devlog_path.parent)
    devlog_path.write_text(
        "# Development log\n\n"
        "Written by the builder, one entry per run. Earlier entries are archived "
        f"under `{_ARCHIVE_DIR.as_posix()}/`; the most recent archive is "
        f"[{archive_path.name}]({rel.as_posix()}).\n",
        encoding="utf-8",
    )
    return archive_path


def append(devlog_path: Path, status: str, task: str, detail: str) -> None:
    """Append a ``## <time> — <status>: <task>`` section with ``detail`` body."""
    existing = devlog_path.read_text(encoding="utf-8") if devlog_path.exists() else ""
    if len(existing.encode("utf-8")) > MAX_DEVLOG_BYTES:
        archived = _rotate(devlog_path)
        print(f"devlog rotated into {archived}")
        existing = devlog_path.read_text(encoding="utf-8")
    header = f"## {_timestamp()} — {status}: {task}"
    body = detail.strip() or "(no detail)"
    entry = f"\n{header}\n\n{body}\n"
    devlog_path.write_text(existing + entry, encoding="utf-8")
