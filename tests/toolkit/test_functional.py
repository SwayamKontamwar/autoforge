from app.toolkit.functional import compose


def test_compose_basic_two_functions() -> None:
    def add_one(x: int) -> int:
        return x + 1

    def mul_two(x: int) -> int:
        return x * 2

    # compose(add_one, mul_two)(3) == add_one(mul_two(3)) == 7
    assert compose(add_one, mul_two)(3) == 7


def test_compose_right_to_left_order() -> None:
    # str after len: should return the string representation of the length
    assert compose(str, len)("abc") == "3"


def test_compose_single_function() -> None:
    def square(x: int) -> int:
        return x * x

    assert compose(square)(5) == 25


def test_compose_no_functions_is_identity() -> None:
    identity = compose()
    assert identity(42) == 42
    assert identity("hello", extra=1) == "hello"
    assert identity() is None


def test_compose_multiple_args_first_function() -> None:
    def sum_two(a: int, b: int) -> int:
        return a + b

    def double(x: int) -> int:
        return x * 2

    # sum_two receives two args, double receives the result
    assert compose(double, sum_two)(2, 3) == 10
