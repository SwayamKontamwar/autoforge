"""Simple deterministic finite state machine.

The :class:`StateMachine` class provides a minimal yet useful abstraction for
defining a set of *states*, a mapping of *transitions* between those states, and
a *current* state.  It is deliberately lightweight: only the features required
by the test suite are implemented.

Typical usage::

    sm = StateMachine(
        states=["idle", "running", "finished"],
        initial="idle",
        transitions={
            ("idle", "start"): "running",
            ("running", "stop"): "finished",
        },
    )
    assert sm.state == "idle"
    sm.trigger("start")
    assert sm.state == "running"

The implementation validates inputs and raises :class:`ValueError` for
invalid operations (unknown states, undefined transitions, etc.).
"""

from __future__ import annotations

from collections.abc import Hashable, Mapping
from typing import Any, Dict, Tuple


class StateMachine:
    """A minimal deterministic finite state machine.

    Parameters
    ----------
    states:
        An iterable of hashable identifiers representing the possible states.
    initial:
        The starting state; must be present in *states*.
    transitions:
        Mapping of ``(state, event)`` tuples to the resulting state.
        ``state`` must be in *states* and the resulting state must also be in
        *states*.

    Methods
    -------
    trigger(event):
        Perform a transition based on the current state and *event*.
    add_state(state):
        Add a new state to the machine.
    add_transition(state, event, next_state):
        Register a new transition.
    """

    __slots__ = ("_states", "_transitions", "_state")

    def __init__(
        self,
        *,
        states: Any,
        initial: Hashable,
        transitions: Mapping[Tuple[Hashable, Any], Hashable] | None = None,
    ) -> None:
        self._states = set(states)
        if not self._states:
            raise ValueError("StateMachine must have at least one state")
        if initial not in self._states:
            raise ValueError(f"Initial state {initial!r} not in states")
        self._state = initial
        self._transitions: Dict[Tuple[Hashable, Any], Hashable] = {}
        if transitions:
            for (src, ev), dst in transitions.items():
                self.add_transition(src, ev, dst)

    @property
    def state(self) -> Hashable:
        """Current state."""
        return self._state

    def trigger(self, event: Any) -> None:
        """Advance the machine using *event*.

        Raises
        ------
        ValueError
            If there is no transition defined for ``(current_state, event)``.
        """
        key = (self._state, event)
        if key not in self._transitions:
            raise ValueError(
                f"No transition defined for state {self._state!r} with event {event!r}"
            )
        self._state = self._transitions[key]

    def add_state(self, state: Hashable) -> None:
        """Add *state* to the set of known states."""
        self._states.add(state)

    def add_transition(self, src: Hashable, event: Any, dst: Hashable) -> None:
        """Register a transition from *src* to *dst* on *event*.

        Both *src* and *dst* must be known states; otherwise a :class:`ValueError`
        is raised.
        """
        if src not in self._states:
            raise ValueError(f"Source state {src!r} not known")
        if dst not in self._states:
            raise ValueError(f"Destination state {dst!r} not known")
        self._transitions[(src, event)] = dst

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(state={self._state!r})"
