"""The committed attempt-state file must never be able to stop the loop.

``.forge/state.json`` is committed, so damage to it is not a transient glitch: it
comes back on every future checkout. If reading it can raise, the run dies before
it can do any work -- and dies again on the next run, and every run after that,
with no path to self-repair. These tests pin both halves of the defence: reads
tolerate a damaged file, and writes cannot produce one in the first place.
"""

from __future__ import annotations

import json
from pathlib import Path

from builder import run


def test_a_truncated_write_does_not_stop_the_run(tmp_path: Path) -> None:
    """A kill mid-write can split a multi-byte character, so decoding fails first."""
    state = tmp_path / "state.json"
    state.write_bytes(b'{"__last_failures__": {"t": "guardrail said \xe2\x80')

    assert run._load_state(state) == {}


def test_invalid_json_does_not_stop_the_run(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    state.write_text('{"a": 1', encoding="utf-8")

    assert run._load_state(state) == {}


def test_a_non_object_payload_does_not_stop_the_run(tmp_path: Path) -> None:
    """Valid JSON of the wrong shape would otherwise crash on the first .get()."""
    state = tmp_path / "state.json"
    state.write_text("[1, 2, 3]", encoding="utf-8")

    assert run._load_state(state) == {}


def test_a_missing_file_is_simply_empty(tmp_path: Path) -> None:
    assert run._load_state(tmp_path / "nope.json") == {}


def test_saving_replaces_the_file_atomically(tmp_path: Path, monkeypatch) -> None:
    """The real file must never be opened for writing, only swapped into place."""
    state = tmp_path / ".forge" / "state.json"
    run._save_state(state, {"a": 1})
    swapped: list[str] = []
    real_replace = run.os.replace

    def _tracked(src, dst):
        swapped.append(str(dst))
        return real_replace(src, dst)

    monkeypatch.setattr(run.os, "replace", _tracked)
    run._save_state(state, {"a": 2})

    assert swapped == [str(state)]
    assert json.loads(state.read_text(encoding="utf-8")) == {"a": 2}
    assert not (state.parent / "state.json.tmp").exists()


def test_a_saved_state_round_trips(tmp_path: Path) -> None:
    state = tmp_path / ".forge" / "state.json"
    payload = {"task — with punctuation": 2, "__last_failures__": {"t": "log"}}

    run._save_state(state, payload)

    assert run._load_state(state) == payload
