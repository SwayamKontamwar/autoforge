import dataclasses
from typing import List, Optional

from app.toolkit.serialization import dataclass_to_dict


@dataclasses.dataclass
class Inner:
    x: int
    y: str = "default"


@dataclasses.dataclass
class Outer:
    a: Inner
    b: List[Inner]
    c: dict[str, Inner]
    d: Optional[int] = None


def test_dataclass_to_dict_nested() -> None:
    inner1 = Inner(1)
    inner2 = Inner(2, "custom")
    outer = Outer(
        a=inner1,
        b=[inner1, inner2],
        c={"first": inner1, "second": inner2},
        d=5,
    )
    result = dataclass_to_dict(outer)
    expected = {
        "a": {"x": 1, "y": "default"},
        "b": [{"x": 1, "y": "default"}, {"x": 2, "y": "custom"}],
        "c": {
            "first": {"x": 1, "y": "default"},
            "second": {"x": 2, "y": "custom"},
        },
        "d": 5,
    }
    assert result == expected


def test_dataclass_to_dict_none_and_empty() -> None:
    outer = Outer(a=Inner(0), b=[], c={}, d=None)
    result = dataclass_to_dict(outer)
    expected = {
        "a": {"x": 0, "y": "default"},
        "b": [],
        "c": {},
        "d": None,
    }
    assert result == expected
