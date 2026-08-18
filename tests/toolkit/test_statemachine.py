import pytest

from app.toolkit.statemachine import StateMachine


def test_statemachine_basic_flow() -> None:
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
    sm.trigger("stop")
    assert sm.state == "finished"


def test_statemachine_invalid_operations() -> None:
    # Initial state not in states raises
    with pytest.raises(ValueError):
        StateMachine(states=["A", "B"], initial="C", transitions={})

    sm = StateMachine(states=["X", "Y"], initial="X", transitions={})
    # Triggering undefined transition raises
    with pytest.raises(ValueError):
        sm.trigger("unknown")

    # Adding a transition with unknown states raises
    with pytest.raises(ValueError):
        sm.add_transition("X", "toZ", "Z")

    # Properly add a transition and use it
    sm.add_state("Z")
    sm.add_transition("X", "toZ", "Z")
    sm.trigger("toZ")
    assert sm.state == "Z"
