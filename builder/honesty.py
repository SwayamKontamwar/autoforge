"""Reject work that makes the guardrail lie instead of making the code right.

The guardrail asks one question -- does the suite pass? -- and a model that
cannot solve a task can always answer it the wrong way: not by writing working
code, but by changing what "passing" means.

This is not hypothetical. Asked to add ``GET /stats``, the bot failed twice on a
test written against the wrong ``httpx`` keyword, and on the third attempt
shipped no endpoint and no test at all -- only a monkey-patch of FastAPI's
``TestClient`` inside ``app/__init__.py``, rewriting the argument so its earlier
mistake would be accepted. Lint passed, the import passed, the suite passed, the
task was ticked off, and the DEVLOG recorded a success. Nothing was built, and
production code now patched a testing library at import time.

That is the worst failure shape this project can have: not a red run, which the
loop already handles, but a green one that is wrong. Nobody is watching, so a
green run is never re-examined.

Both checks here are deliberately narrow. They target a patch tampering with the
machinery that judges it, not a patch that is merely bad -- ordinary mistakes are
the guardrail's job, and rejecting honest work is its own kind of damage.
"""

from __future__ import annotations

import ast

# Importing any of these from production code is a category error: they exist to
# exercise an application, not to be part of one. This is also the narrowest
# reliable signature of the incident above.
TEST_ONLY_MODULES = (
    "pytest",
    "unittest",
    "fastapi.testclient",
    "starlette.testclient",
    "httpx._client",
    "_pytest",
)

# Rebinding an attribute on one of these replaces the harness the verdict comes
# from, wherever it happens.
_HARNESS_NAMES = frozenset(
    {
        "TestClient",
        "pytest",
        "unittest",
        "_pytest",
        "ruff",
        "TestCase",
    }
)

PRODUCTION_PREFIX = "app/"


def _root_module(name: str) -> str:
    return name.split(".", 1)[0]


def _imports_test_only(tree: ast.AST) -> str | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in TEST_ONLY_MODULES or _root_module(
                    alias.name
                ) in TEST_ONLY_MODULES:
                    return alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module in TEST_ONLY_MODULES or _root_module(node.module) in TEST_ONLY_MODULES:
                return node.module
            for alias in node.names:
                if f"{node.module}.{alias.name}" in TEST_ONLY_MODULES:
                    return f"{node.module}.{alias.name}"
    return None


def _patches_harness(tree: ast.AST) -> str | None:
    """Find ``SomeHarness.method = ...``, however the name was aliased.

    Aliases matter: the real incident bound ``TestClient`` to
    ``_FastAPITestClient`` first, so matching the imported name alone would have
    missed it entirely.
    """
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                if alias.name in _HARNESS_NAMES or node.module in TEST_ONLY_MODULES:
                    aliases.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if _root_module(alias.name) in _HARNESS_NAMES:
                    aliases.add(alias.asname or alias.name.split(".")[0])

    targets = aliases | _HARNESS_NAMES
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Attribute):
                continue
            base = target.value
            if isinstance(base, ast.Name) and base.id in targets:
                return f"{base.id}.{target.attr}"
    return None


def rigged_verdict_reason(files) -> str | None:
    """Explain why a patch is judging itself, or ``None`` if it is honest.

    Unparseable input is ignored on purpose. A file that will not parse cannot be
    tampering with anything, and it is about to fail lint and import anyway --
    reporting it from this check would blame the wrong thing.

    The exception list is wide because the input is untrusted model output, not
    source anyone wrote. A lone surrogate raises ``UnicodeEncodeError`` out of
    ``ast.parse``, a null byte raises ``ValueError``, and deeply nested brackets
    can exhaust the stack in either ``parse`` or ``walk``. Any of those escaping
    would be an unhandled traceback in a log nobody reads -- the same task failing
    identically forever, which is precisely what this project must not do.
    """
    for file in files:
        path = file.path.replace("\\", "/")
        if not path.endswith(".py"):
            continue
        try:
            tree = ast.parse(file.content)

            if path.startswith(PRODUCTION_PREFIX):
                imported = _imports_test_only(tree)
                if imported:
                    return (
                        f"{path} imports {imported}, which is a testing tool. Production "
                        f"code must not import the harness that judges it. If a test "
                        f"needs different behaviour, change the test."
                    )

            patched = _patches_harness(tree)
        except (SyntaxError, ValueError, RecursionError, MemoryError):
            continue

        if patched:
            return (
                f"{path} reassigns {patched}, which replaces part of the test harness "
                f"rather than making the code correct. Fix the code or the test; do "
                f"not change what passing means."
            )
    return None


def untested_production_reason(files, tests_before: int, tests_after: int) -> str | None:
    """Explain why a patch shipped production code that nothing verifies.

    The old rule only rejected a suite that *shrank*, so adding no tests at all
    scored the same as adding good ones -- which is exactly how a task with no
    implementation and no test was marked done. Every task in this backlog asks
    for a test by name, so on a feature patch a flat count means the work was
    never demonstrated.

    Counts of ``-1`` mean pytest could not be collected. That is unknown, not
    zero, and guessing either way would be worse than declining to judge.
    """
    if tests_before < 0 or tests_after < 0:
        return None
    touches_production = any(
        file.path.replace("\\", "/").startswith(PRODUCTION_PREFIX) for file in files
    )
    if not touches_production or tests_after > tests_before:
        return None
    return (
        f"the patch changed production code under {PRODUCTION_PREFIX} but the suite "
        f"still collects {tests_after} tests, so nothing new proves the work. Add a "
        f"test that fails without this change."
    )
