# SPDX-License-Identifier: Apache-2.0
"""The type of a rule that was read from a rule file."""

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import PurePosixPath

    from wio.models.config import RulePreset

_FAMILY_AND_NUMBER = re.compile(r"([A-Z]+)([0-9]+)")


@dataclass(frozen=True)
class Rule:
    """One atomic do-or-don't instruction, read from a rule file.

    A rule is immutable and hashable, so it can be a key of a mapping. Two rules
    are equal when every field is.

    Attributes:
        ruleset: The name of the ruleset whose directory holds the file.
        code: The rule's code, a family of upper-case letters and digits, such
            as `ARC001`.
        name: The rule's name, lower-case words joined by single hyphens.
        description: The one-line description in the metadata block, if any.
        summary: The lines of the body's first paragraph, each stripped and
            joined with single spaces; empty when there is no body.
        body: The text after the metadata block without its leading and
            trailing blank lines and without a final line ending, with the line
            endings the file has.
        body_line: The line of the file, counted from 1, on which the body
            starts, or the line after the block when the body is empty.
        path: The path of the file as the reader was given it.
    """

    ruleset: str
    code: str
    name: str
    description: str | None
    summary: str
    body: str
    body_line: int
    path: PurePosixPath

    @property
    def family(self) -> str:
        """The upper-case letters of the code, such as `ARC`."""
        return self._parts()[0]

    @property
    def number(self) -> int:
        """The digits of the code as a number, such as 1 for `ARC001`."""
        return int(self._parts()[1])

    @property
    def qualified(self) -> str:
        """The code with its ruleset, such as `demo.ARC001`."""
        return f"{self.ruleset}.{self.code}"

    def _parts(self) -> tuple[str, str]:
        """Split the code into its family and its digits."""
        found = _FAMILY_AND_NUMBER.fullmatch(self.code)
        if found is None:
            message = f"`{self.code}` is not a family and digits"
            raise ValueError(message)
        return found[1], found[2]


@dataclass(frozen=True)
class Manifest:
    """What a ruleset's `ruleset.toml` declares.

    It is immutable and hashable, because its mappings are frozen. A manifest may
    declare nothing: a ruleset can be started before its first rule.

    Attributes:
        description: What the ruleset is for, or `None` when it has none.
        families: The topic of each family, by the upper-case letters of the
            family, in the order written.
        rule_presets: The ruleset's rule presets by name, each with the
            `rules_include` and `rules_exclude` of the config's rule preset, in
            the order written.
    """

    description: str | None = None
    families: frozendict[str, str] = field(default=frozendict())
    rule_presets: frozendict[str, RulePreset] = field(default=frozendict())


@dataclass(frozen=True)
class LoadedRuleset:
    """A ruleset of the repository with its manifest and the rules it holds.

    It is immutable and hashable. It is not the `Ruleset` of `wio.models.config`,
    which holds the settings that the config gives a ruleset.

    Attributes:
        name: The name of the ruleset's directory, which is its canonical name.
        path: The path of the directory relative to the repository root.
        manifest: What the ruleset's `ruleset.toml` declares.
        rules: The rules in the order of family, then the number of the code,
            then the text of the code, so `ARC999` comes before `ARC1000` and
            `ARC001` before `ARC01`.
    """

    name: str
    path: PurePosixPath
    manifest: Manifest
    rules: tuple[Rule, ...]

    def rules_of(self, family: str) -> tuple[Rule, ...]:
        """Find the rules of one family.

        Args:
            family: The upper-case letters of the family, such as `ARC`.

        Returns:
            The rules of the family in the order of `rules`; none for a family
            that no rule has.
        """
        return tuple(rule for rule in self.rules if rule.family == family)

    def get(self, code: str) -> Rule | None:
        """Find a rule by its code.

        Args:
            code: The code as written, such as `ARC2`; `ARC02` is another code.

        Returns:
            The rule with exactly that code, or `None`.
        """
        for rule in self.rules:
            if rule.code == code:
                return rule
        return None
