from app.toolkit.functional import pipe


def test_pipe_basic_two_functions() -> None:
    def add_one(x: int) -> int:
        return x + 1

    def mul_two(x: int) -> int:
        return x * 2

    # pipe(add_one, mul_two)(3) == mul_two(add_one(3)) == 8
    assert pipe(add_one, mul_two)(3) == 8


def test_pipe_left_to_right_order() -> None:
    # len then str: should return the string representation of the length
    assert pipe(len, str)("abc") == "3"


def test_pipe_single_function() -> None:
    def square(x: int) -> int:
        return x * x

    assert pipe(square)(5) == 25


def test_pipe_no_functions_is_identity() -> None:
    identity = pipe()
    assert identity(42) == 42
    assert identity("hello", extra=1) == "hello"
    assert identity() is None


def test_pipe_multiple_args_first_function() -> None:
    def sum_two(a: int, b: int) -> int:
        return a + b

    def double(x: int) -> int:
        return x * 2

    # sum_two receives two args, double receives the result
    assert pipe(sum_two, double)(2, 3) == 10
