# SPDX-License-Identifier: Apache-2.0
"""The expansion of a rule preset, a family or a code into the rules it selects.

It works on values alone: the rulesets, their aliases and the config's rule
presets reach it as a `RuleCatalog`, so it reads no file and the same catalog
and entries always give the same expansion. The four layers and the roots that
apply are built on it elsewhere, and reporting a problem as a diagnostic is for
`wio rules check`.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.models.config import RulePreset
    from wio.models.rule import LoadedRuleset, Rule
    from wio.models.rules import Route, Routes


@dataclass(frozen=True)
class ConfigScope:
    """The scope of the config's entries, where a bare name is a rule preset.

    An item of a ruleset is written `<ruleset>.<item>`, with the ruleset's name
    or alias.
    """


@dataclass(frozen=True)
class RulesetScope:
    """The scope of a manifest's entries, which name the ruleset's own items.

    Attributes:
        name: The canonical name of the ruleset. A bare name is a family, a code
            or a rule preset of that ruleset.
    """

    name: str


type Scope = ConfigScope | RulesetScope


@dataclass(frozen=True)
class RuleCatalog:
    """What the references of an expansion are resolved in.

    Attributes:
        rulesets: The rulesets by canonical name.
        aliases: Each alias mapped to the canonical name it stands for.
        presets: The config's rule presets by name.
    """

    rulesets: Mapping[str, LoadedRuleset] = field(default=frozendict())
    aliases: Mapping[str, str] = field(default=frozendict())
    presets: Mapping[str, RulePreset] = field(default=frozendict())


type ProblemKind = Literal["unknown", "malformed", "qualified-in-manifest", "cycle"]
"""What is wrong with an entry that could not be expanded."""


@dataclass(frozen=True)
class Problem:
    """An entry that could not be expanded.

    Attributes:
        kind: `unknown` for an entry that names nothing, `malformed` for text
            that is not a reference, `qualified-in-manifest` for `<ruleset>.<item>`
            inside a manifest, and `cycle` for a rule preset that includes
            itself.
        reference: The entry as written.
        route: The rule presets it was found in, outermost first, empty for an
            entry of the list that was expanded; for a cycle it ends with the
            rule preset that closes it.
    """

    kind: ProblemKind
    reference: str
    route: Route


@dataclass(frozen=True)
class Expansion:
    """The rules that a list of entries selects, and how.

    It is immutable and hashable: `expand` builds the mappings as `frozendict`s,
    and a caller that builds one does the same. The rules are in the order of
    ruleset name, family, number of the code and text of the code.

    Attributes:
        rules: The rules selected, each with every route that selected it.
        removed: The rules that an exclude took out, each with every route of
            the removal. An exclude removes from the includes of its own list,
            and that of a nested rule preset does not reach outside that preset,
            so a rule is in both `rules` and `removed` when one entry includes
            it and an exclude inside another entry's preset names it.
        rulesets: The canonical names of the rulesets that an include entry
            named, nested rule presets included, even when the excludes leave
            none of their rules; an exclude entry and an entry that names
            nothing name none.
        problems: What could not be expanded, sorted by route, then reference,
            then kind. An entry with a problem selects nothing and the others
            are still expanded.
    """

    rules: Mapping[Rule, Routes]
    removed: Mapping[Rule, Routes]
    rulesets: frozenset[str]
    problems: tuple[Problem, ...]


def expand(
    include: Sequence[str],
    exclude: Sequence[str],
    scope: Scope,
    catalog: RuleCatalog,
) -> Expansion:
    """Expand a list of includes and excludes into the rules it selects.

    The includes are expanded, then the excludes are expanded and removed from
    them. An entry is a family, a code or a rule preset, and a rule preset takes
    its own includes and then removes its own excludes; its entries are read in
    the scope of its own ruleset, or of the config. A ruleset has a rule preset
    `all` that holds all its rules, whatever its manifest says of that name. A
    family that its manifest declares and that holds no rule selects nothing and
    is no problem. The grammar of an entry is that of `wio.formats.grammar`: a
    bare upper-case name is malformed in the config's scope, and
    `parse_own_item` reads the entries of a manifest.

    It does no input or output and raises nothing for an entry or a cycle, and
    the result does not depend on the order of the tables of the catalog or of
    the entries of a list.

    Args:
        include: The references to select, as written.
        exclude: The references to remove from what the includes select.
        scope: What a bare name is.
        catalog: The rulesets, aliases and rule presets to resolve them in.

    Returns:
        The expansion.
    """
    del include, exclude, scope
    msg = f"expand over {len(catalog.rulesets)} rulesets is declared by architecture"
    raise NotImplementedError(msg)
