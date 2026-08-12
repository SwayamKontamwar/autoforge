"""Simple command‑line argument parser.

The ``parse_args_simple`` function converts a flat list of arguments of the form
``--key value`` into a ``dict`` mapping each *key* (without the leading dashes)
to its corresponding *value* (as a string).

Only the minimal behaviour required by the test suite is implemented:

* Every option must start with ``--``.
* Each option must be followed by a value that does **not** start with ``--``.
* Duplicate keys are allowed – the last occurrence wins.
* If an option is missing a value, ``ValueError`` is raised.

Example
-------
>>> parse_args_simple(["--name", "alice", "--age", "30"])
{'name': 'alice', 'age': '30'}
"""

from __future__ import annotations

from typing import Dict, List


def parse_args_simple(args: List[str]) -> Dict[str, str]:
    """Parse a list of ``--key value`` arguments into a dictionary.

    Args:
        args: List of command‑line arguments (e.g. ``sys.argv[1:]``).

    Returns:
        Mapping of option names to their string values.

    Raises:
        ValueError: If an argument does not start with ``--`` or a value is
            missing.
    """
    result: Dict[str, str] = {}
    i = 0
    length = len(args)

    while i < length:
        arg = args[i]
        if not arg.startswith("--"):
            raise ValueError(f"Unexpected argument without leading '--': {arg!r}")
        key = arg.lstrip("-")
        i += 1
        if i >= length:
            raise ValueError(f"Missing value for option '--{key}'")
        value = args[i]
        if value.startswith("--"):
            raise ValueError(f"Missing value for option '--{key}'")
        result[key] = value
        i += 1

    return result
