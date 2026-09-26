from app.toolkit import deep_get


def test_deep_get_simple():
    data = {"a": {"b": {"c": 42}}}
    assert deep_get(data, "a.b.c") == 42


def test_deep_get_missing_key_returns_default():
    data = {"a": {"b": 1}}
    assert deep_get(data, "a.x.c", default="missing") == "missing"


def test_deep_get_non_dict_intermediate():
    data = {"a": 5}
    assert deep_get(data, "a.b", default=None) is None


def test_deep_get_empty_path_returns_default():
    data = {"key": "value"}
    assert deep_get(data, "", default="default") == "default"
