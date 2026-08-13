import json

import pytest

from app.toolkit.serialization import to_jsonl


def test_to_jsonl_typical() -> None:
    data = [{"a": 1}, {"b": [2, 3]}, "string"]
    result = to_jsonl(data)
    expected = "\n".join(json.dumps(item, ensure_ascii=False) for item in data)
    assert result == expected


def test_to_jsonl_empty_iterable() -> None:
    assert to_jsonl([]) == ""


def test_to_jsonl_non_serializable_raises() -> None:
    class NotSerializable:
        pass

    with pytest.raises(TypeError):
        to_jsonl([NotSerializable()])
