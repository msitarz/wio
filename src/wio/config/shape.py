# SPDX-License-Identifier: Apache-2.0
"""The shape of the config file: its keys, types and values, read from the schema."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast

from wio.config import messages
from wio.config.schema import (
    Atom,
    Choice,
    Open,
    PresetOrStages,
    Slot,
    Spec,
    Strings,
    Table,
    schema,
    tables,
)
from wio.models.config import Config, Stage
from wio.models.diagnostics import Diagnostic
from wio.models.frozen import freeze

if TYPE_CHECKING:
    from collections.abc import Mapping

type Source = Literal["file", "default"]


@dataclass(frozen=True)
class Shape:
    """What the walk of a decoded file built.

    Attributes:
        config: The best-effort `Config`: an invalid value has its default, an
            unknown key and an entry of the wrong type are dropped, and a root
            or an action that lacks a required key keeps it empty.
        diagnostics: One error for each problem of the shape, in no order.
        sources: The source of each leaf key path that has a value.
    """

    config: Config
    diagnostics: tuple[Diagnostic, ...]
    sources: frozendict[str, Source]


class _Dropped:
    """The marker of a value that was invalid and is not kept."""


DROPPED = _Dropped()


def read_shape(data: dict[str, object]) -> Shape:
    """Walk the dataclasses of `Config` over a decoded config file.

    One walk builds the value, the diagnostics of its shape and the source of
    each key path from the same schema, so none can drift from the fields.

    Args:
        data: The decoded file, as `decode_toml` returns it.

    Returns:
        The best-effort `Config`, every problem of the shape and the sources.
    """
    walk = _Walk()
    config = cast("Config", walk.table(schema(), data, ""))
    return Shape(config, tuple(walk.found), freeze(walk.sources))


class _Walk:
    """One walk over a decoded file, which collects what it finds."""

    def __init__(self) -> None:
        """Start with no diagnostics and no sources."""
        self.found: list[Diagnostic] = []
        self.sources: dict[str, Source] = {}

    def error(self, where: str, message: str) -> None:
        """Record an error.

        Args:
            where: The key path.
            message: What is wrong and how to fix it.
        """
        self.found.append(Diagnostic("error", where, message))

    def table(self, spec: Table, raw: Mapping[str, object], path: str) -> object:
        """Build one table from its keys.

        Args:
            spec: The table's schema.
            raw: The keys the file sets in it, none for a table it omits.
            path: The key path of the table.

        Returns:
            The dataclass of the table, filled as far as the file allows.
        """
        self._unknown(spec, raw, path)
        values = {slot.name: self._slot(slot, raw, path) for slot in spec.slots}
        built = spec.build(**values)
        if isinstance(built, Stage):
            self._goal_or_skill(raw, path)
        return built

    def _unknown(self, spec: Table, raw: Mapping[str, object], path: str) -> None:
        """Report each key the table does not have.

        Args:
            spec: The table's schema.
            raw: The keys the file sets.
            path: The key path of the table.
        """
        valid = [slot.name for slot in spec.slots]
        for key in raw:
            if key not in valid:
                elsewhere = _elsewhere(key, spec)
                text = messages.unknown_key(key, spec, valid, elsewhere)
                self.error(messages.join_path(path, key), text)

    def _goal_or_skill(self, raw: Mapping[str, object], path: str) -> None:
        """Report a stage that sets both or neither of `goal` and `skill`.

        Args:
            raw: The keys the stage sets.
            path: The key path of the stage.
        """
        count = ("goal" in raw) + ("skill" in raw)
        if count != 1:
            self.error(path, messages.goal_or_skill(both=count == 2))

    def _slot(self, slot: Slot, raw: Mapping[str, object], path: str) -> object:
        """Read the value of one key, or give it its default.

        Args:
            slot: The key.
            raw: The keys the file sets in the table.
            path: The key path of the table.

        Returns:
            The value, or what stands in for a missing or invalid one.
        """
        where = messages.join_path(path, slot.name)
        if slot.name in raw:
            value = self.value(slot.spec, raw[slot.name], where, slot.description)
            if not isinstance(value, _Dropped):
                self._note(slot, where, value, "file")
                return value
        elif slot.required:
            self.error(path, f"missing key `{slot.name}`. {slot.description}")
        return self._fallback(slot, where)

    def _fallback(self, slot: Slot, where: str) -> object:
        """Give a key its default, or an empty value when it is required.

        Args:
            slot: The key.
            where: Its key path.

        Returns:
            The value, with its source recorded as the default.
        """
        match slot.spec:
            case Table() as spec:
                return self.table(spec, {}, where)
            case Open():
                return frozendict()
            case _:
                value = slot.empty if slot.required else slot.default
                self._note(slot, where, value, "default")
                return value

    def _note(self, slot: Slot, where: str, value: object, source: Source) -> None:
        """Record the source of a leaf setting that has a value.

        Args:
            slot: The key.
            where: Its key path.
            value: What the key holds.
            source: Whether it came from the file or is the default.
        """
        leaf = not isinstance(slot.spec, Table | Open)
        if leaf and value is not None:
            self.sources[where] = source

    def value(self, spec: Spec, raw: object, where: str, description: str) -> object:
        """Read one value against its spec.

        Args:
            spec: What the value looks like.
            raw: What the file holds.
            where: The key path.
            description: The setting's description, for the message.

        Returns:
            The value, or `DROPPED` after recording why it cannot be kept.
        """
        if messages.is_temporal(raw):
            self.error(
                where,
                f"no setting holds a date or a time, received {raw}. {description}",
            )
            return DROPPED
        match spec:
            case Table() | Open() as nested:
                return self._nested(nested, raw, where, description)
            case Strings():
                return self._strings(raw, where, description)
            case PresetOrStages():
                return self._preset(spec, raw, where, description)
            case Choice():
                return self._choice(spec, raw, where, description)
            case Atom(kind):
                return self._atom(spec, kind, raw, where, description)

    def _atom(
        self, spec: Atom, kind: type, raw: object, where: str, description: str
    ) -> object:
        """Read a string, a boolean or an integer, which are never coerced.

        Args:
            spec: The atom.
            kind: The exact type a value must have.
            raw: What the file holds.
            where: The key path.
            description: The setting's description.

        Returns:
            The value, or `DROPPED`.
        """
        if type(raw) is kind:
            return raw
        self.error(where, messages.wrong_type(raw, spec, description))
        return DROPPED

    def _choice(
        self, spec: Choice, raw: object, where: str, description: str
    ) -> object:
        """Read a string of a vocabulary.

        Args:
            spec: The vocabulary.
            raw: What the file holds.
            where: The key path.
            description: The setting's description.

        Returns:
            The string, or `DROPPED`.
        """
        if isinstance(raw, str) and raw in spec.values:
            return raw
        if isinstance(raw, str):
            self.error(where, messages.wrong_value(raw, spec, description))
        else:
            self.error(where, messages.wrong_type(raw, spec, description))
        return DROPPED

    def _strings(self, raw: object, where: str, description: str) -> object:
        """Read a list of strings, dropping the items that are not strings.

        Args:
            raw: What the file holds.
            where: The key path.
            description: The setting's description.

        Returns:
            The strings as a tuple, or `DROPPED` when the value is not a list.
        """
        if not isinstance(raw, list):
            self.error(where, messages.wrong_type(raw, Strings(), description))
            return DROPPED
        items = (
            self.value(Atom(str), item, messages.item_path(where, index), description)
            for index, item in enumerate(raw)
        )
        return tuple(item for item in items if not isinstance(item, _Dropped))

    def _preset(self, spec: Spec, raw: object, where: str, description: str) -> object:
        """Read a stage preset id or a list of stage names.

        Args:
            spec: The preset-or-stages spec.
            raw: What the file holds.
            where: The key path.
            description: The setting's description.

        Returns:
            The string or the tuple, or `DROPPED`.
        """
        if isinstance(raw, str):
            return raw
        if isinstance(raw, list):
            return self._strings(raw, where, description)
        self.error(where, messages.wrong_type(raw, spec, description))
        return DROPPED

    def _nested(
        self, spec: Table | Open, raw: object, where: str, description: str
    ) -> object:
        """Read a table, or a table of named entries.

        Args:
            spec: The table or the open table.
            raw: What the file holds.
            where: The key path.
            description: The setting's description.

        Returns:
            The built value, or `DROPPED` when the value is not a table.
        """
        if not isinstance(raw, dict):
            self.error(where, messages.wrong_type(raw, spec, description))
            return DROPPED
        if isinstance(spec, Table):
            return self.table(spec, raw, where)
        return self._entries(spec, raw, where, description)

    def _entries(
        self, spec: Open, raw: Mapping[str, object], where: str, description: str
    ) -> object:
        """Read the named entries of an open table.

        Args:
            spec: The open table.
            raw: The entries the file sets.
            where: The key path of the open table.
            description: The setting's description.

        Returns:
            A frozen mapping of the entries that could be kept.
        """
        kept: dict[str, object] = {}
        for name, entry in raw.items():
            path = messages.join_path(where, name)
            value = self.value(spec.value, entry, path, description)
            if not isinstance(value, _Dropped):
                kept[name] = value
                self._note_entry(spec.value, path)
        return freeze(kept)

    def _note_entry(self, spec: Spec, path: str) -> None:
        """Record an entry of an open table as set by the file, if it is a leaf.

        Args:
            spec: What the entry looks like.
            path: Its key path.
        """
        if not isinstance(spec, Table | Open):
            self.sources[path] = "file"


def _elsewhere(key: str, here: Table) -> list[str]:
    """Name the other tables of the schema that have a key.

    Args:
        key: The unknown key.
        here: The table the key was found in, left out.

    Returns:
        How a message names each other table with a key of that name.
    """
    return [
        other.noun
        for other in tables(schema())
        if other is not here and any(slot.name == key for slot in other.slots)
    ]
