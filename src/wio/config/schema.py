# SPDX-License-Identifier: Apache-2.0
"""The schema of the config file, derived from the dataclasses of `Config`.

The schema is built once from the fields and annotations of `Config`, so a new
field is a new key without a second place to declare it.
"""

import builtins
import dataclasses
import re
import types
import typing
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING, Any

from wio.models.config import Config

if TYPE_CHECKING:
    from collections.abc import Callable

type Spec = Atom | Choice | Strings | PresetOrStages | Table | Open


@dataclass(frozen=True)
class Atom:
    """A string, a boolean or an integer.

    Attributes:
        kind: The Python type a value must have exactly.
    """

    kind: type


@dataclass(frozen=True)
class Choice:
    """A string that is one of a fixed vocabulary.

    Attributes:
        values: The allowed strings, in the order the field declares them.
    """

    values: tuple[str, ...]


@dataclass(frozen=True)
class Strings:
    """A list of strings."""


@dataclass(frozen=True)
class PresetOrStages:
    """A stage preset id, or a list of stage names."""


@dataclass(frozen=True)
class Slot:
    """One key of a table.

    Attributes:
        name: The key, which is the name of the field.
        spec: What a value of the key looks like.
        description: The field's one-sentence description.
        default: The field's default, `None` when it has none.
        required: Whether the key must be set because the field has no default.
        empty: The value a required key that is missing or invalid is given.
    """

    name: str
    spec: Spec
    description: str
    default: object
    required: bool
    empty: object


@dataclass(frozen=True)
class Table:
    """A table: a fixed set of keys, each a field of a dataclass.

    Attributes:
        build: The dataclass the table becomes.
        noun: How a message names the table, such as `a stage`.
        slots: The keys, in the order of the fields.
    """

    build: Callable[..., object]
    noun: str
    slots: tuple[Slot, ...]


@dataclass(frozen=True)
class Open:
    """A table whose keys are names, each holding a value of one spec.

    Attributes:
        value: What the value of each name looks like.
    """

    value: Spec


@cache
def schema() -> Table:
    """Build the schema of the whole config.

    Returns:
        The table of the top level, which holds every other table and key.
    """
    return _table(Config, "the top level of the config", "")


def tables(top: Table) -> list[Table]:
    """List a table and every table below it, in the order of the fields.

    Args:
        top: The table to start from.

    Returns:
        `top`, then the tables its keys hold, depth first.
    """
    found = [top]
    for slot in top.slots:
        spec = slot.spec.value if isinstance(slot.spec, Open) else slot.spec
        if isinstance(spec, Table):
            found += tables(spec)
    return found


def _table(build: type, noun: str, path: str) -> Table:
    """Build the table of a dataclass.

    Args:
        build: The dataclass.
        noun: How a message names the table.
        path: The key path of the table, for naming the tables below it.

    Returns:
        The table, with a slot for each field.
    """
    hints = typing.get_type_hints(build)
    slots = tuple(
        _slot(item, hints[item.name], f"{path}.{item.name}".lstrip("."))
        for item in dataclasses.fields(build)
    )
    return Table(build, noun, slots)


def _slot(item: dataclasses.Field[Any], hint: object, path: str) -> Slot:
    """Build the slot of one field.

    Args:
        item: The field.
        hint: Its resolved annotation.
        path: Its key path.

    Returns:
        The slot.
    """
    spec = _spec(hint, path)
    required = item.default is dataclasses.MISSING
    default = None if required else item.default
    return Slot(
        item.name,
        spec,
        str(item.metadata["description"]),
        default,
        required,
        _empty(spec),
    )


def _spec(hint: object, path: str) -> Spec:
    """Derive what a value looks like from an annotation.

    Args:
        hint: The annotation, such as `tuple[str, ...] | None`.
        path: The key path of the field, for naming a nested table.

    Returns:
        The spec of the annotation, without its `None`.
    """
    args = typing.get_args(hint)
    match typing.get_origin(hint):
        case types.UnionType:
            return _union([arg for arg in args if arg is not type(None)], path)
        case typing.Literal:
            return Choice(tuple(str(arg) for arg in args))
        case builtins.tuple:
            return Strings()
        case builtins.frozendict:
            return Open(_member(args[1], path))
        case _:
            return _plain(hint, path)


def _plain(hint: object, path: str) -> Spec:
    """Derive the spec of an annotation that is no generic.

    Args:
        hint: A class, such as `str` or a dataclass.
        path: The key path of the field.

    Returns:
        A table for a dataclass, otherwise an atom of the class.
    """
    if dataclasses.is_dataclass(hint) and isinstance(hint, type):
        return _table(hint, f"`[{path}]`", path)
    return Atom(hint if isinstance(hint, type) else str)


def _union(args: list[Any], path: str) -> Spec:
    """Derive the spec of a union without `None`.

    Args:
        args: The members of the union.
        path: The key path of the field.

    Returns:
        The spec of the one member, or the preset-or-stages spec of a union of a
        string and a list of strings.
    """
    if len(args) == 1:
        return _spec(args[0], path)
    return PresetOrStages()


def _member(hint: object, path: str) -> Spec:
    """Derive the spec of a value of an open table.

    Args:
        hint: The annotation of the value.
        path: The key path of the open table.

    Returns:
        The spec; a dataclass is a table named after its class, such as `a root`.
    """
    if dataclasses.is_dataclass(hint) and isinstance(hint, type):
        return _table(hint, _noun(hint.__name__), f"{path}.<name>")
    return _spec(hint, path)


def _noun(name: str) -> str:
    """Name a table after its class.

    Args:
        name: A class name such as `RulePreset`.

    Returns:
        The words of the name with an article, such as `a rule preset`.
    """
    words = re.sub(r"(?<!^)(?=[A-Z])", " ", name).lower()
    article = "an" if words[0] in "aeiou" else "a"
    return f"{article} {words}"


def _empty(spec: Spec) -> object:
    """Give the value that stands for a required key that is not usable.

    Args:
        spec: What a value of the key looks like.

    Returns:
        An empty string for a string, an empty tuple for a list, and `None` for
        anything else.
    """
    match spec:
        case Atom(kind):
            return kind()
        case Strings():
            return ()
        case _:
            return None
