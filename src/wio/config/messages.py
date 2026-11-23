# SPDX-License-Identifier: Apache-2.0
"""The words of the diagnostics of the shape and the key paths they name."""

import datetime
from typing import TYPE_CHECKING

from wio.config.schema import Atom, Choice, Open, PresetOrStages, Spec, Strings, Table
lazy from wio.formats import and_list, closest_key, quote_string, quoted

if TYPE_CHECKING:
    from collections.abc import Sequence


def show(value: object) -> str:
    """Show a received value the way TOML writes it, or by its kind.

    Args:
        value: What the file holds.

    Returns:
        A scalar as written, and `a list` or `a table` for the rest.
    """
    match value:
        case bool():
            return "true" if value else "false"
        case str():
            return quote_string(value)
        case int() | float():
            return str(value)
        case list():
            return "a list"
        case dict():
            return "a table"
        case _:
            return type(value).__name__


def expected(spec: Spec) -> str:
    """Say what kind of value a spec takes.

    Args:
        spec: What a value looks like.

    Returns:
        A phrase such as `a string` or `a list of strings`.
    """
    match spec:
        case Atom(kind) if kind is bool:
            return "a boolean"
        case Atom(kind) if kind is int:
            return "an integer"
        case Strings():
            return "a list of strings"
        case Table(noun=noun):
            return f"a table ({noun})"
        case Open():
            return "a table"
        case _:
            return "a string"


def is_temporal(value: object) -> bool:
    """Tell whether a decoded value is a TOML date, time or date-time.

    Args:
        value: What the file holds.

    Returns:
        True for a `date`, `time` or `datetime`.
    """
    return isinstance(value, datetime.date | datetime.time)


def wrong_type(value: object, spec: Spec, description: str) -> str:
    """Build the message of a value of the wrong type.

    Args:
        value: What the file holds.
        spec: What the key takes.
        description: The setting's description.

    Returns:
        The received value, the expected kind and the description.
    """
    if isinstance(spec, PresetOrStages):
        found = f"received {show(value)}; a value is a stage preset id or a list of"
        return f"{found} stage names. {description}"
    allowed = ""
    if isinstance(spec, Choice):
        allowed = f"; allowed {and_list([quote_string(v) for v in spec.values])}"
    return f"received {show(value)}, expected {expected(spec)}{allowed}. {description}"


def wrong_value(value: object, spec: Choice, description: str) -> str:
    """Build the message of a string outside its vocabulary.

    Args:
        value: What the file holds.
        spec: The vocabulary.
        description: The setting's description.

    Returns:
        The received value, the allowed values and the description.
    """
    allowed = and_list([quote_string(v) for v in spec.values])
    return f"received {show(value)}, allowed {allowed}. {description}"


def unknown_key(
    key: str, table: Table, valid: Sequence[str], elsewhere: Sequence[str]
) -> str:
    """Build the message of a key the schema does not know.

    Args:
        key: The unknown key.
        table: The table it is in.
        valid: The keys the table has.
        elsewhere: How a message names each other table that has the key.

    Returns:
        The key, the valid keys, the closest match and where the key belongs.
    """
    message = f"unknown key `{key}` in {table.noun}. Valid keys: {quoted(valid)}."
    close = closest_key(key, valid)
    if close:
        message += f" Did you mean `{close}`?"
    if elsewhere:
        message += f" `{key}` is a key of {and_list(elsewhere)}."
    return message


def goal_or_skill(both: bool) -> str:  # noqa: FBT001
    """Build the message of a stage with both or neither of `goal` and `skill`.

    Args:
        both: True when the stage sets both, false when it sets neither.

    Returns:
        What `goal` and `skill` are, and that exactly one is needed.
    """
    found = "sets both" if both else "sets neither"
    return (
        "a stage needs exactly one of `goal`, what the stage does in prose, and "
        f"`skill`, the skill that carries it; this one {found}."
    )
