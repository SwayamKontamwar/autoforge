"""Tests for keeping BACKLOG.md readable without losing history."""

from __future__ import annotations

from pathlib import Path

from builder import backlog


def _write_backlog(path: Path, done: int, open_items: int, pad: int = 300) -> None:
    lines = ["# Backlog", ""]
    lines += [f"- [x] completed task {i} {'x' * pad}" for i in range(done)]
    lines += [f"- [ ] open task {i} {'y' * pad}" for i in range(open_items)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_small_backlog_is_left_alone(tmp_path) -> None:
    path = tmp_path / "BACKLOG.md"
    _write_backlog(path, done=3, open_items=3)
    assert backlog.archive_completed(path) is None
    assert "- [x] completed task 0" in path.read_text(encoding="utf-8")


def test_a_long_backlog_of_pending_work_is_not_archived_every_run(tmp_path) -> None:
    """A big file is not the same as a big *completed* section.

    The curated seed alone is ~288KB of pending work. Triggering on total size
    would move a handful of finished items out on every single run, committing a
    new archive file each time and never shrinking anything.
    """
    path = tmp_path / "BACKLOG.md"
    _write_backlog(path, done=3, open_items=1200)
    assert path.stat().st_size > 300_000
    assert backlog.archive_completed(path) is None


def test_oversized_backlog_moves_completed_items_out_without_losing_them(tmp_path) -> None:
    path = tmp_path / "BACKLOG.md"
    _write_backlog(path, done=900, open_items=50)
    archive = backlog.archive_completed(path)

    assert archive is not None and archive.exists()
    live = path.read_text(encoding="utf-8")
    archived = archive.read_text(encoding="utf-8")
    assert "- [x] completed task 0" not in live
    assert "- [x] completed task 899" in archived
    assert "- [ ] open task 0" in live
    assert archive.name in live


def test_archived_tasks_still_block_duplicates(tmp_path) -> None:
    """The dedup set must span the archive.

    If archiving hid finished work, the generator would immediately hand back
    tasks the project had already completed and it would start rebuilding itself
    in circles.
    """
    path = tmp_path / "BACKLOG.md"
    _write_backlog(path, done=900, open_items=50)
    before = backlog.all_task_texts(path)

    backlog.archive_completed(path)

    assert backlog.all_task_texts(path) == before
    assert any(t.startswith("completed task 0 ") for t in backlog.all_task_texts(path))


def test_next_task_still_works_after_archiving(tmp_path) -> None:
    path = tmp_path / "BACKLOG.md"
    _write_backlog(path, done=900, open_items=50)
    backlog.archive_completed(path)

    task = backlog.next_task(path)
    assert task is not None and task.text.startswith("open task 0")

    backlog.mark_done(path, task.index)
    assert "- [x] open task 0" in path.read_text(encoding="utf-8")


def test_repeated_archiving_numbers_files_and_never_overwrites(tmp_path) -> None:
    path = tmp_path / "BACKLOG.md"
    _write_backlog(path, done=900, open_items=50)
    first = backlog.archive_completed(path)
    _write_backlog(path, done=900, open_items=50)
    second = backlog.archive_completed(path)

    assert first is not None and second is not None
    assert first != second
    assert first.exists() and second.exists()
