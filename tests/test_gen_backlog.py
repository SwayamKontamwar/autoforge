"""The curated backlog generator is a human tool pointed at a live repository.

Two things can quietly ruin years of history: rewriting a backlog that already
holds finished work (the bot would be handed it all back), and shipping a
taxonomy with duplicate unit names (every toolkit unit is re-exported from one
`app/toolkit/__init__.py`, so a collision silently shadows an earlier build).
"""

import importlib.util
from pathlib import Path

import pytest

_SOURCE = Path(__file__).resolve().parent.parent / "tools" / "gen_backlog.py"


def _load():
    spec = importlib.util.spec_from_file_location("gen_backlog_under_test", _SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load()


def test_refuses_to_reopen_completed_work(tmp_path, capsys):
    backlog = tmp_path / "BACKLOG.md"
    original = "# Backlog\n\n- [x] Build the thing\n- [ ] Build the other thing\n"
    backlog.write_text(original, encoding="utf-8")

    assert gen.main(["--output", str(backlog)]) == 1
    assert backlog.read_text(encoding="utf-8") == original
    assert "refusing to overwrite" in capsys.readouterr().out


def test_force_overwrites_when_the_caller_insists(tmp_path):
    backlog = tmp_path / "BACKLOG.md"
    backlog.write_text("- [x] Build the thing\n", encoding="utf-8")

    assert gen.main(["--output", str(backlog), "--force"]) == 0
    rewritten = backlog.read_text(encoding="utf-8")
    assert gen.completed_count(backlog) == 0
    assert "Build the thing" not in rewritten
    assert rewritten.count("\n- [ ] ") == gen.task_count()


def test_writes_a_backlog_that_has_no_completed_work(tmp_path):
    backlog = tmp_path / "BACKLOG.md"

    assert gen.main(["--output", str(backlog)]) == 0
    assert backlog.read_text(encoding="utf-8").count("\n- [ ] ") == gen.task_count()


@pytest.mark.parametrize("field", [0, 1])
def test_every_category_entry_is_distinct(field):
    values = [entry[field] for entry in gen.CATEGORIES]
    assert len(values) == len(set(values))


def test_toolkit_unit_names_never_collide():
    names = [name for _, _, items in gen.CATEGORIES for name, _ in items]
    duplicates = {name for name in names if names.count(name) > 1}
    assert not duplicates


def test_generated_tasks_are_unique():
    tasks = gen._interleaved_tasks()
    assert len(tasks) == len(set(tasks))
    assert len(gen.FOUNDATION) == len(set(gen.FOUNDATION))
    assert not set(tasks) & set(gen.FOUNDATION)
    assert len(tasks) + len(gen.FOUNDATION) == gen.task_count()
