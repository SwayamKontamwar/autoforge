import json

import pytest

from app.toolkit.serialization import from_jsonl, to_jsonl


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


def test_from_jsonl_typical() -> None:
    data = [{"a": 1}, {"b": [2, 3]}, "string"]
    text = "\n".join(json.dumps(item, ensure_ascii=False) for item in data)
    assert from_jsonl(text) == data


def test_from_jsonl_trailing_newline_and_empty_lines() -> None:
    data = [{"x": 10}, {"y": 20}]
    text = "\n".join(json.dumps(item) for item in data) + "\n\n"
    assert from_jsonl(text) == data


def test_from_jsonl_invalid_json_raises() -> None:
    bad = '{"a": 1}\\nnotjson\\n{"b": 2}'
    with pytest.raises(json.JSONDecodeError):
        from_jsonl(bad)
