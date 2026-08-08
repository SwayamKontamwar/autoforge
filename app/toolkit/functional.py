"""Functional utilities for the toolkit.

This module currently provides a simple function composition helper.
"""

from __future__ import annotations

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
