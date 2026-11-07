# SPDX-License-Identifier: Apache-2.0
"""The words of the diagnostics of the shape and the key paths they name."""

import datetime
import re
from typing import TYPE_CHECKING
lazy import difflib

from wio.config.schema import Atom, Choice, Open, PresetOrStages, Spec, Strings, Table

if TYPE_CHECKING:
    from collections.abc import Sequence

_BARE = re.compile(r"[A-Za-z0-9_-]+")


def join_path(parent: str, key: str) -> str:
    """Add a key to a key path, quoting it as TOML does when it needs it.

    Args:
        parent: The key path so far; empty at the top level.
        key: The key to add.

    Returns:
        The longer key path.
    """
    name = key if _BARE.fullmatch(key) else _quote(key)
    return f"{parent}.{name}" if parent else name


def _quote(key: str) -> str:
    """Quote a key as a TOML basic string.

    Args:
        key: The key.

    Returns:
        The key in double quotes, with backslashes and quotes escaped.
    """
    escaped = key.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def item_path(parent: str, index: int) -> str:
    """Add a list index to a key path.

    Args:
        parent: The key path of the list.
        index: The position of the item.

    Returns:
        The key path of the item, such as `rules_include[0]`.
    """
    return f"{parent}[{index}]"


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
            return _quote(value)
        case int() | float():
            return str(value)
        case list():
            return "a list"
        case dict():
            return "a table"
        case _:
            return type(value).__name__


def quoted(names: Sequence[str]) -> str:
    """Join names in code quotes for a sentence.

    Args:
        names: The names.

    Returns:
        Each name in backticks, joined by commas.
    """
    return ", ".join(f"`{name}`" for name in names)


def and_list(items: Sequence[str]) -> str:
    """Join items as English does.

    Args:
        items: The items, at least one.

    Returns:
        `a`, `a and b` or `a, b and c`.
    """
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"


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
        allowed = f"; allowed {and_list([_quote(v) for v in spec.values])}"
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
    allowed = and_list([_quote(v) for v in spec.values])
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
    close = difflib.get_close_matches(key, valid, n=1)
    if close:
        message += f" Did you mean `{close[0]}`?"
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
