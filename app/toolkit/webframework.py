"""Simple request router for FastAPI‑style path handling.

The router matches HTTP *method* and *path* strings to callables (handlers).
Static routes (no ``{param}`` placeholders) are stored separately and always
take precedence over parameterised routes, regardless of the order they were
added.

Supported path syntax
---------------------

* Static segments, e.g. ``/about``.
* Parameterised segments using ``{name}`` which match any non‑empty sequence of
  characters that does not contain a slash. The captured value is returned in a
  ``dict`` keyed by the parameter name.

Only the features required by the test‑suite are implemented; this is not a
full‑featured router.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, List, Pattern, Tuple

Handler = Callable[..., Any]


def path_to_regex(path: str) -> Pattern[str]:
    """Convert a FastAPI‑style path pattern to a compiled regular expression.

    The pattern may contain ``{name}`` placeholders which are translated into
    named capture groups matching any non‑empty sequence of characters that does
    not contain a slash. All other characters are escaped so that they are
    interpreted literally.

    Parameters
    ----------
    path: str
        The route pattern, e.g. ``"/users/{id}"``.

    Returns
    -------
    Pattern[str]
        A compiled regex that matches the entire path and provides the captured
        parameters via ``match.groupdict()``.
    """
    # Escape everything first, then restore braces for substitution.
    escaped = re.escape(path)
    escaped = escaped.replace(r"\{", "{").replace(r"\}", "}")

    # Find placeholders like {param}
    param_pattern = re.compile(r"{([^}]+)}")

    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        return f"(?P<{name}>[^/]+)"

    regex_body = param_pattern.sub(repl, escaped)
    return re.compile(f"^{regex_body}$")


class _Route:
    __slots__ = ("method", "handler", "is_static", "pattern", "param_names")

    def __init__(self, method: str, path: str, handler: Handler) -> None:
        self.method: str = method.upper()
        self.handler: Handler = handler
        self.is_static: bool = "{" not in path
        self.pattern: Pattern[str] | None = None
        self.param_names: List[str] = []

        if not self.is_static:
            # Convert ``/users/{id}`` → ``^/users/(?P<id>[^/]+)$``
            # Escape regex meta‑characters outside of parameter placeholders.
            escaped = re.escape(path)
            # ``re.escape`` also escapes the braces; we need to restore them for
            # substitution.  A simple approach is to replace the escaped ``\\{``
            # and ``\\}`` pairs with a marker, then substitute.
            escaped = escaped.replace(r"\{", "{").replace(r"\}", "}")
            # Find ``{name}`` placeholders.
            param_pattern = re.compile(r"{([^}]+)}")
            self.param_names = param_pattern.findall(path)

            def repl(match: re.Match[str]) -> str:
                name = match.group(1)
                return f"(?P<{name}>[^/]+)"

            regex_body = param_pattern.sub(repl, escaped)
            self.pattern = re.compile(f"^{regex_body}$")

    def match(self, method: str, path: str) -> Tuple[Handler | None, Dict[str, str]]:
        if self.method != method.upper():
            return None, {}
        if self.is_static:
            # Static routes are compared directly; ``self.pattern`` is None.
            return self.handler, {}
        if self.pattern is None:
            return None, {}
        m = self.pattern.match(path)
        if not m:
            return None, {}
        return self.handler, m.groupdict()


class Router:
    """Minimal router for matching HTTP methods and URL paths to handlers."""

    __slots__ = ("_static_routes", "_param_routes")

    def __init__(self) -> None:
        # Static routes are stored in a dict keyed by (method, path) for O(1)
        # lookup. Parameterised routes are kept in a list preserving insertion
        # order; they are consulted only after static routes have been checked.
        self._static_routes: Dict[Tuple[str, str], Handler] = {}
        self._param_routes: List[_Route] = []

    def add_route(self, method: str, path: str, handler: Handler) -> None:
        """Register *handler* for *method* and *path*.

        If *path* contains ``{`` and ``}`` it is treated as a parameterised route.
        Static routes are stored separately to guarantee precedence.
        """
        route = _Route(method, path, handler)
        if route.is_static:
            self._static_routes[(route.method, path)] = handler
        else:
            self._param_routes.append(route)

    def match(self, method: str, path: str) -> Tuple[Handler | None, Dict[str, str]]:
        """Return ``(handler, params)`` for the first matching route.

        If no route matches, ``handler`` is ``None`` and ``params`` is an empty
        ``dict``.
        """
        key = (method.upper(), path)
        if key in self._static_routes:
            return self._static_routes[key], {}
        for route in self._param_routes:
            handler, params = route.match(method, path)
            if handler is not None:
                return handler, params
        return None, {}


__all__ = ["Router", "path_to_regex"]
