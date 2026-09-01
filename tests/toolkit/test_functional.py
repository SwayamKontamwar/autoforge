from app.toolkit.functional import compose, curry


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


def test_curry_partial_application() -> None:
    def add(a: int, b: int) -> int:
        return a + b

    curried = curry(add)
    add_five = curried(5)
    assert callable(add_five)
    assert add_five(3) == 8


def test_curry_multiple_arguments_at_once() -> None:
    def mul(a: int, b: int, c: int) -> int:
        return a * b * c

    curried = curry(mul)
    # Supplying all arguments in one call should work.
    assert curried(2, 3, 4) == 24
    # Supplying them step‑by‑step also works.
    assert curried(2)(3)(4) == 24
    assert curried(2, 3)(4) == 24
    assert curried(2)(3, 4) == 24


def test_curry_with_keyword_arguments() -> None:
    def greet(greeting: str, name: str) -> str:
        return f"{greeting}, {name}"

    curried = curry(greet)
    step = curried(greeting="Hi")
    assert callable(step)
    assert step(name="Alice") == "Hi, Alice"


def test_curry_zero_argument_function() -> None:
    def constant() -> int:
        return 42

    curried = curry(constant)
    # No arguments needed; calling returns the result immediately.
    assert curried() == 42
