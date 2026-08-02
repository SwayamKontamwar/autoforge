"""Tests for the development log and its rotation.

The log is the human-readable artefact this whole experiment produces, so the
thing that must not happen is it quietly becoming unreadable.
"""

from __future__ import annotations

from pathlib import Path

from builder import devlog


def test_append_adds_a_dated_entry(tmp_path: Path) -> None:
    path = tmp_path / "DEVLOG.md"
    devlog.append(path, "success", "do the thing", "it worked")
    text = path.read_text(encoding="utf-8")
    assert "success: do the thing" in text
    assert "it worked" in text


def test_small_logs_are_not_rotated(tmp_path: Path) -> None:
    path = tmp_path / "DEVLOG.md"
    for i in range(20):
        devlog.append(path, "success", f"task {i}", "fine")
    assert not (tmp_path / "docs" / "devlog").exists()
    assert "task 0" in path.read_text(encoding="utf-8")


def test_oversized_log_is_archived_not_lost(tmp_path: Path) -> None:
    """At three entries a day this fires within about eighteen months.

    GitHub stops rendering markdown around a megabyte, so without rotation the
    project's most readable artefact turns into an error message in the web UI.
    """
    path = tmp_path / "DEVLOG.md"
    oversized = "# Development log\n" + ("x" * (devlog.MAX_DEVLOG_BYTES + 10))
    path.write_text(oversized, encoding="utf-8")

    devlog.append(path, "success", "after rotation", "fresh entry")

    archives = sorted((tmp_path / "docs" / "devlog").glob("devlog-*.md"))
    assert len(archives) == 1, "the old log must be archived, never discarded"
    assert "x" * 100 in archives[0].read_text(encoding="utf-8"), "history lost in rotation"

    current = path.read_text(encoding="utf-8")
    assert len(current.encode("utf-8")) < devlog.MAX_DEVLOG_BYTES
    assert "after rotation" in current, "the entry that triggered rotation must still land"
    assert archives[0].name in current, "the fresh log must link back to the archive"
    assert "x" * 100 not in current


def test_repeated_rotations_do_not_overwrite_each_other(tmp_path: Path) -> None:
    path = tmp_path / "DEVLOG.md"
    for marker in ("first", "second", "third"):
        path.write_text(marker + "y" * (devlog.MAX_DEVLOG_BYTES + 10), encoding="utf-8")
        devlog.append(path, "success", f"entry after {marker}", "ok")

    archives = sorted((tmp_path / "docs" / "devlog").glob("devlog-*.md"))
    assert len(archives) == 3, "each rotation needs its own file"
    contents = [a.read_text(encoding="utf-8")[:6] for a in archives]
    assert sorted(c.rstrip("y") for c in contents) == ["first", "second", "third"]
