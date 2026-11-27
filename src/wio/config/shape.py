# SPDX-License-Identifier: Apache-2.0
"""The shape of the config file: its keys, types and values, read from the schema."""

from dataclasses import dataclass, replace
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
from wio.formats.wording import item_path, join_path
from wio.models.config import Config, Log, Stage
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

    The log settings use open-table defaults keyed by harness name. A name
    present in the file replaces its whole default entry. The walk reports
    the source of both leaf settings for an inherited entry as `default`,
    using the same key paths as it does for entries from the file. A
    configured harness with a missing or empty session list gets one shape
    diagnostic at the session key path. The later checks leave the empty
    fallback alone so it does not produce another diagnostic.

    Args:
        data: The decoded file, as `decode_toml` returns it.

    Returns:
        The best-effort `Config`, every problem of the shape and the sources.
    """
    walk = _Walk()
    config = cast("Config", walk.table(schema(), data, ""))
    config = replace(config, log=walk.with_builtin_harnesses(config.log))
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

    def with_builtin_harnesses(self, log: Log) -> Log:
        """Keep configured entries and record the leaves inherited from defaults.

        Args:
            log: Log settings with the harness entries read from the file.

        Returns:
            Settings with a complete harness mapping. Each configured entry
            replaces its built-in as a whole, including omitted parent variables.
        """
        builtins = Log().harnesses
        for name in builtins.keys() - log.harnesses.keys():
            path = join_path("log.harnesses", name)
            self.sources[f"{path}.session"] = "default"
            self.sources[f"{path}.parent"] = "default"
        return replace(log, harnesses=freeze(builtins | log.harnesses))

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
        """Report each key the table does not have."""
        valid = [slot.name for slot in spec.slots]
        for key in raw:
            if key not in valid:
                elsewhere = _elsewhere(key, spec)
                text = messages.unknown_key(key, spec, valid, elsewhere)
                self.error(join_path(path, key), text)

    def _goal_or_skill(self, raw: Mapping[str, object], path: str) -> None:
        """Report a stage that sets both or neither of `goal` and `skill`."""
        count = ("goal" in raw) + ("skill" in raw)
        if count != 1:
            self.error(path, messages.goal_or_skill(both=count == 2))

    def _slot(self, slot: Slot, raw: Mapping[str, object], path: str) -> object:
        """Read the value of one key, or give it its default."""
        where = join_path(path, slot.name)
        if slot.name in raw:
            value = self.value(slot.spec, raw[slot.name], where, slot.description)
            if not isinstance(value, _Dropped):
                self._note(slot, where, value, "file")
                return value
        elif slot.required:
            at = (
                where if isinstance(slot.spec, Strings) and slot.spec.nonempty else path
            )
            self.error(at, f"missing key `{slot.name}`. {slot.description}")
        return self._fallback(slot, where)

    def _fallback(self, slot: Slot, where: str) -> object:
        """Give a key its default, or an empty value when it is required."""
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
        """Record the source of a leaf setting that has a value."""
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
            case Strings(nonempty=True) if raw == []:
                self.error(where, f"expected at least one string. {description}")
                return DROPPED
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
        """Read a string, a boolean or an integer, which are never coerced."""
        if type(raw) is kind:
            return raw
        self.error(where, messages.wrong_type(raw, spec, description))
        return DROPPED

    def _choice(
        self, spec: Choice, raw: object, where: str, description: str
    ) -> object:
        """Read a string of a vocabulary."""
        if isinstance(raw, str) and raw in spec.values:
            return raw
        if isinstance(raw, str):
            self.error(where, messages.wrong_value(raw, spec, description))
        else:
            self.error(where, messages.wrong_type(raw, spec, description))
        return DROPPED

    def _strings(self, raw: object, where: str, description: str) -> object:
        """Read a list of strings, dropping the items that are not strings."""
        if not isinstance(raw, list):
            self.error(where, messages.wrong_type(raw, Strings(), description))
            return DROPPED
        items = (
            self.value(Atom(str), item, item_path(where, index), description)
            for index, item in enumerate(raw)
        )
        return tuple(item for item in items if not isinstance(item, _Dropped))

    def _preset(self, spec: Spec, raw: object, where: str, description: str) -> object:
        """Read a stage preset id or a list of stage names."""
        if isinstance(raw, str):
            return raw
        if isinstance(raw, list):
            return self._strings(raw, where, description)
        self.error(where, messages.wrong_type(raw, spec, description))
        return DROPPED

    def _nested(
        self, spec: Table | Open, raw: object, where: str, description: str
    ) -> object:
        """Read a table, or a table of named entries."""
        if not isinstance(raw, dict):
            self.error(where, messages.wrong_type(raw, spec, description))
            return DROPPED
        if isinstance(spec, Table):
            return self.table(spec, raw, where)
        return self._entries(spec, raw, where, description)

    def _entries(
        self, spec: Open, raw: Mapping[str, object], where: str, description: str
    ) -> object:
        """Read the named entries of an open table."""
        kept: dict[str, object] = {}
        for name, entry in raw.items():
            path = join_path(where, name)
            value = self.value(spec.value, entry, path, description)
            if not isinstance(value, _Dropped):
                kept[name] = value
                self._note_entry(spec.value, path)
        return freeze(kept)

    def _note_entry(self, spec: Spec, path: str) -> None:
        """Record an entry of an open table as set by the file, if it is a leaf."""
        if not isinstance(spec, Table | Open):
            self.sources[path] = "file"


def _elsewhere(key: str, here: Table) -> list[str]:
    """Name the other tables of the schema that have a key."""
    return [
        other.noun
        for other in tables(schema())
        if other is not here and any(slot.name == key for slot in other.slots)
    ]
