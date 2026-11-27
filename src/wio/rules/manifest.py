# SPDX-License-Identifier: Apache-2.0
"""The reader of a ruleset's manifest, which turns one `ruleset.toml` into data.

It does no input or output and reads only the text it is given, so finding the
file and judging what it declares against the rule files are for the caller.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.formats.errors import TomlSyntaxError
from wio.formats.grammar import FAMILY, NAME
from wio.formats.wording import item_path, join_path, quoted
from wio.models.config import RulePreset
from wio.models.diagnostics import Diagnostic, sort_diagnostics
from wio.models.frozen import freeze
from wio.models.rule import Manifest
lazy from wio.formats import closest_key, decode_toml

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from pathlib import PurePosixPath

_KEYS = ("description", "families", "rule_presets")
_PRESET_KEYS = ("rules_include", "rules_exclude")


@dataclass(frozen=True)
class ManifestReading:
    """What reading one `ruleset.toml` gave.

    Attributes:
        manifest: The manifest, or `None` when the text has an error.
        diagnostics: Every error and warning of the text, in the order of
            `sort_diagnostics`.
    """

    manifest: Manifest | None
    diagnostics: tuple[Diagnostic, ...]


def read_manifest(path: PurePosixPath, text: str) -> ManifestReading:
    """Read the text of a `ruleset.toml` into a manifest.

    Reuses `decode_toml` and `closest_key` of `wio.formats`, the forms of a
    family and a rule preset name of `wio.formats.grammar`, and `join_path` and
    `item_path` of `wio.formats.wording` for the places of the faults.

    Args:
        path: The path of the file relative to the repository root.
        text: The text of the file, decoded as UTF-8; an empty text is an empty
            manifest.

    Returns:
        The manifest, with the families and the rule presets in the order
        written, and no error when the text has the shape of a manifest. Each
        fault is one error and leaves the manifest out: text that does not parse
        is at the path followed by `:<line>`, and any other fault is at the path
        followed by `#` and the key path of the fault, such as `#description`
        or `#rule_presets.x.rules_include[0]`. A key that the manifest or a rule
        preset does not know is a warning at the same kind of place that names
        the key and the closest known key, and the manifest is still returned.
    """
    try:
        data = decode_toml(text)
    except TomlSyntaxError as error:
        fault = Diagnostic("error", f"{path}:{error.line}", error.message)
        return ManifestReading(None, (fault,))
    reader = _Reader(f"{path}#")
    manifest = reader.read(data)
    found = sort_diagnostics(reader.found)
    if any(d.severity == "error" for d in found):
        return ManifestReading(None, found)
    return ManifestReading(manifest, found)


class _Reader:
    """The judging of one decoded manifest, which collects what it finds."""

    def __init__(self, prefix: str) -> None:
        """Start a reading.

        Args:
            prefix: The manifest's path followed by `#`, which each place starts
                with.
        """
        self.prefix = prefix
        self.found: list[Diagnostic] = []

    def error(self, key_path: str, message: str) -> None:
        """Record an error at a key path.

        Args:
            key_path: The key path of the fault.
            message: What is wrong.
        """
        self.found.append(Diagnostic("error", self.prefix + key_path, message))

    def read(self, data: Mapping[str, object]) -> Manifest:
        """Judge a decoded manifest and build what is valid of it.

        Args:
            data: The decoded TOML.

        Returns:
            The manifest of the valid parts; it is only used when no error was
            recorded.
        """
        self._unknown(data, "", _KEYS)
        description = data.get("description")
        if "description" in data and not isinstance(description, str):
            self.error("description", "`description` must be a string.")
        return Manifest(
            description=description if isinstance(description, str) else None,
            families=freeze(dict(self._families(data.get("families")))),
            rule_presets=freeze(dict(self._presets(data.get("rule_presets")))),
        )

    def _unknown(
        self, data: Mapping[str, object], parent: str, known: tuple[str, ...]
    ) -> None:
        """Warn of the keys of a table that it does not know."""
        for key in data:
            if key in known:
                continue
            message = f"unknown key `{key}`. Valid keys: {quoted(known)}."
            close = closest_key(key, known)
            if close:
                message += f" Did you mean `{close}`?"
            where = self.prefix + join_path(parent, key)
            self.found.append(Diagnostic("warning", where, message))

    def _families(self, value: object) -> Iterator[tuple[str, str]]:
        """Judge the `families` table."""
        if value is None:
            return
        if not isinstance(value, dict):
            self.error("families", "`families` must be a table of topics.")
            return
        for family, topic in value.items():
            where = join_path("families", family)
            if not FAMILY.fullmatch(family):
                self.error(
                    where, f"`{family}` is not a family; use upper-case letters."
                )
            elif not isinstance(topic, str):
                self.error(where, f"the topic of `{family}` must be a string.")
            else:
                yield family, topic

    def _presets(self, value: object) -> Iterator[tuple[str, RulePreset]]:
        """Judge the `rule_presets` table."""
        if value is None:
            return
        if not isinstance(value, dict):
            self.error("rule_presets", "`rule_presets` must be a table of presets.")
            return
        for name, table in value.items():
            where = join_path("rule_presets", name)
            if not NAME.fullmatch(name):
                self.error(where, f"`{name}` is not a rule preset name.")
            elif not isinstance(table, dict):
                self.error(where, f"the rule preset `{name}` must be a table.")
            else:
                yield name, self._preset(where, table)

    def _preset(self, where: str, table: Mapping[str, object]) -> RulePreset:
        """Judge one rule preset."""
        self._unknown(table, where, _PRESET_KEYS)
        include = self._list(
            join_path(where, "rules_include"), table.get("rules_include")
        )
        exclude = self._list(
            join_path(where, "rules_exclude"), table.get("rules_exclude")
        )
        return RulePreset(include, exclude)

    def _list(self, where: str, value: object) -> tuple[str, ...]:
        """Judge a list of strings."""
        if value is None:
            return ()
        if not isinstance(value, list):
            self.error(
                where, f"`{where.rsplit('.', 1)[-1]}` must be a list of strings."
            )
            return ()
        for index, entry in enumerate(value):
            if not isinstance(entry, str):
                self.error(item_path(where, index), "an entry must be a string.")
        return tuple(entry for entry in value if isinstance(entry, str))
