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


def confirm_prompt(prompt: str, default: bool | None = None) -> bool:
    """Prompt the user for a yes/no answer.

    The function reads a line from ``input(prompt)`` and interprets it as a
    boolean decision.

    * Accepted affirmative responses (case‑insensitive): ``y``, ``yes``.
    * Accepted negative responses (case‑insensitive): ``n``, ``no``.
    * If the user enters an empty string and *default* is not ``None``, the
      default value is returned.
    * Otherwise a ``ValueError`` is raised for empty input without a default
      or for any unrecognised response.

    Args:
        prompt: The prompt string displayed to the user.
        default: The value to return when the user provides no input. If ``None``,
            empty input is considered an error.

    Returns:
        ``True`` for an affirmative answer, ``False`` for a negative answer.

    Raises:
        ValueError: If the input is empty and no default is supplied, or if the
            input cannot be interpreted as yes/no.
    """
    response = input(prompt).strip().lower()
    if not response:
        if default is not None:
            return default
        raise ValueError("No input provided and no default set")
    if response in {"y", "yes"}:
        return True
    if response in {"n", "no"}:
        return False
    raise ValueError(f"Invalid response: {response!r}")
