"""Appending dated entries to the development log.

Every run — success or failure — leaves an honest, timestamped record so the
git history reads like a real engineering journal rather than opaque bot noise.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def append(devlog_path: Path, status: str, task: str, detail: str) -> None:
    """Append a ``## <time> — <status>: <task>`` section with ``detail`` body."""
    header = f"## {_timestamp()} — {status}: {task}"
    body = detail.strip() or "(no detail)"
    entry = f"\n{header}\n\n{body}\n"
    existing = devlog_path.read_text(encoding="utf-8") if devlog_path.exists() else ""
    devlog_path.write_text(existing + entry, encoding="utf-8")
