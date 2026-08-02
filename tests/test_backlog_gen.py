"""Tests for backlog helpers and the self-replenishing generator."""

from __future__ import annotations

from pathlib import Path

from builder import backlog, backlog_gen


def _make_toolkit(root: Path, module: str, body: str) -> None:
    toolkit = root / "app" / "toolkit"
    toolkit.mkdir(parents=True, exist_ok=True)
    (toolkit / "__init__.py").write_text("", encoding="utf-8")
    (toolkit / f"{module}.py").write_text(body, encoding="utf-8")


def test_open_count_and_task_texts(tmp_path: Path) -> None:
    path = tmp_path / "BACKLOG.md"
    path.write_text(
        "# Backlog\n- [ ] alpha\n- [x] beta  _(done)_\n- [ ] gamma\n",
        encoding="utf-8",
    )
    assert backlog.open_count(path) == 2
    assert backlog.all_task_texts(path) == {"alpha", "beta", "gamma"}


def test_append_tasks_adds_open_items(tmp_path: Path) -> None:
    path = tmp_path / "BACKLOG.md"
    path.write_text("# Backlog\n- [ ] first\n", encoding="utf-8")
    backlog.append_tasks(path, ["second", "third"], heading="More")
    assert backlog.open_count(path) == 3
    assert "## More" in path.read_text(encoding="utf-8")


def test_list_units_skips_private_and_init(tmp_path: Path) -> None:
    _make_toolkit(
        tmp_path,
        "sample",
        "def public():\n    pass\n\n\ndef _private():\n    pass\n\n\nclass Widget:\n    pass\n",
    )
    units = backlog_gen.list_units(tmp_path)
    assert ("sample", "public") in units
    assert ("sample", "Widget") in units
    assert all(name != "_private" for _, name in units)


def test_deterministic_tasks_dedupes(tmp_path: Path) -> None:
    units = [("strings", "slugify")]
    first_theme = backlog_gen._RENEWABLE_THEMES[0].format(module="strings", name="slugify")
    tasks = backlog_gen.deterministic_tasks(units, existing={first_theme}, count=5)
    assert first_theme not in tasks
    assert len(tasks) == len(backlog_gen._RENEWABLE_THEMES) - 1
    assert all("slugify" in task for task in tasks)


def test_replenish_is_never_empty(tmp_path: Path) -> None:
    path = tmp_path / "BACKLOG.md"
    path.write_text("# Backlog\n", encoding="utf-8")
    tasks = backlog_gen.replenish(tmp_path, path, count=10)
    assert tasks  # falls back to a generic task when the toolkit is empty


def test_replenish_uses_toolkit(tmp_path: Path) -> None:
    _make_toolkit(tmp_path, "maths", "def add(a, b):\n    return a + b\n")
    path = tmp_path / "BACKLOG.md"
    path.write_text("# Backlog\n", encoding="utf-8")
    tasks = backlog_gen.replenish(tmp_path, path, count=10)
    assert any("add" in task and "maths" in task for task in tasks)


def _drain(path: Path) -> None:
    """Mark every open task done, as it would be years into a run."""
    lines = path.read_text(encoding="utf-8").splitlines()
    done = [ln.replace("- [ ] ", "- [x] ", 1) for ln in lines]
    path.write_text("\n".join(done) + "\n", encoding="utf-8")


def test_replenish_never_repeats_a_task(tmp_path: Path) -> None:
    """The failure that ends a self-refilling backlog is silent repetition.

    A tiny toolkit exhausts the renewable pool almost immediately, which is exactly
    when a generator is tempted to hand back the same filler task forever. Every
    cycle here must contribute work that has never been seen before.
    """
    _make_toolkit(tmp_path, "maths", "def add(a, b):\n    return a + b\n")
    path = tmp_path / "BACKLOG.md"
    path.write_text("# Backlog\n", encoding="utf-8")

    for _ in range(25):
        _drain(path)
        before = backlog.all_task_texts(path)
        tasks = backlog_gen.replenish(tmp_path, path, count=5)
        assert tasks, "replenish went dry; the loop would starve"
        assert len(set(tasks)) == len(tasks), "replenish repeated itself within one batch"
        assert not (set(tasks) & before), "replenish handed back work already on the list"
        backlog.append_tasks(path, tasks, heading="Auto-generated follow-up work")
        assert backlog.open_count(path) == len(tasks)

    texts = [
        ln.strip()
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.strip().startswith(("- [ ] ", "- [x] "))
    ]
    assert len(set(texts)) == len(texts), "the backlog accumulated duplicate tasks"


def test_replenish_survives_a_missing_toolkit(tmp_path: Path) -> None:
    """With nothing built yet there is no renewable pool at all, and it still holds."""
    path = tmp_path / "BACKLOG.md"
    path.write_text("# Backlog\n", encoding="utf-8")
    produced: set[str] = set()
    for _ in range(10):
        tasks = backlog_gen.replenish(tmp_path, path, count=3)
        assert tasks
        assert not (set(tasks) & produced)
        produced.update(tasks)
        backlog.append_tasks(path, tasks, heading="More")
        _drain(path)


def test_novel_module_tasks_are_unique_by_construction() -> None:
    first = backlog_gen.novel_module_tasks(existing=set(), count=3)
    assert len(set(first)) == 3
    second = backlog_gen.novel_module_tasks(existing=set(first), count=3)
    assert not (set(second) & set(first))
