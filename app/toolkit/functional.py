"""Functional utilities for the toolkit.

This module currently provides a simple function composition helper and a
pipeline helper.  The new ``curry`` function transforms a callable into its
curried form, allowing partial application of arguments.
"""

from __future__ import annotations

from inspect import Parameter, signature
from typing import Any, Callable


def compose(*functions: Callable[..., Any]) -> Callable[..., Any]:
    """Return a function that composes the given callables right‑to‑left.

    ``compose(f, g, h)(*args, **kwargs)`` is equivalent to
    ``f(g(h(*args, **kwargs)))``.  If no functions are supplied, the returned
    callable behaves as an identity function, returning its first positional
    argument (or ``None`` if called without arguments).

    Args:
        *functions: Callables to compose.  They are applied from the last
            argument to the first, i.e. right‑to‑left.

    Returns:
        A new callable representing the composition.
    """
    if not functions:

        def identity(*args: Any, **kwargs: Any) -> Any:
            if args:
                return args[0]
            return None

        return identity

    def composed(*args: Any, **kwargs: Any) -> Any:
        # Apply the right‑most function with the original arguments.
        result = functions[-1](*args, **kwargs)
        # Apply the remaining functions leftwards, each receiving the previous result.
        for fn in reversed(functions[:-1]):
            result = fn(result)
        return result

    return composed


def pipe(*functions: Callable[..., Any]) -> Callable[..., Any]:
    """Return a function that composes the given callables left‑to‑right.

    ``pipe(f, g, h)(*args, **kwargs)`` is equivalent to
    ``h(g(f(*args, **kwargs)))``.  If no functions are supplied, the returned
    callable behaves as an identity function, returning its first positional
    argument (or ``None`` if called without arguments).

    Args:
        *functions: Callables to compose.  They are applied from the first
            argument to the last, i.e. left‑to‑right.

    Returns:
        A new callable representing the left‑to‑right composition.
    """
    if not functions:

        def identity(*args: Any, **kwargs: Any) -> Any:
            if args:
                return args[0]
            return None

        return identity

    def piped(*args: Any, **kwargs: Any) -> Any:
        # Apply the left‑most function with the original arguments.
        result = functions[0](*args, **kwargs)
        # Apply the remaining functions leftwards, each receiving the previous result.
        for fn in functions[1:]:
            result = fn(result)
        return result

    return piped


def curry(func: Callable[..., Any]) -> Callable[..., Any]:
    """Return a curried version of *func*.

    The returned callable accepts arguments incrementally until the original
    function's required positional parameters are satisfied, at which point it
    invokes *func* with the accumulated arguments and any supplied keyword
    arguments.

    Example:
        >>> def add(a, b): return a + b
        >>> curried_add = curry(add)
        >>> add_one = curried_add(1)
        >>> add_one(2)  # returns 3
        3

    Args:
        func: The callable to curry. It should have a fixed number of required
            positional arguments (no ``*args`` handling).

    Returns:
        A new callable that can be partially applied.
    """
    sig = signature(func)
    required_params = [
        p
        for p in sig.parameters.values()
        if p.kind in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
        and p.default is Parameter.empty
    ]
    required_count = len(required_params)

    def _curried(*args: Any, **kwargs: Any) -> Any:
        # If we already have enough arguments to satisfy required positional
        # parameters, call the original function.
        if len(args) + len(kwargs) >= required_count:
            return func(*args, **kwargs)
        # Otherwise, return a new function that collects more arguments.
        return lambda *more_args, **more_kwargs: _curried(
            *args, *more_args, **{**kwargs, **more_kwargs}
        )

    return _curried
