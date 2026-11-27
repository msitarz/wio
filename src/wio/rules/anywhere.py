# SPDX-License-Identifier: Apache-2.0
"""The rules that some include entry of the config delivers, and which entries.

The layers and the decisions answer for one stage and one set of roots. This
module answers for the whole config: which rules any include entry delivers,
whatever the roots and whether or not a pipeline uses the stage, so a listing
can name the rules that nothing selects. It reads no file.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from wio.models.frozen import freeze
from wio.rules.expansion import ConfigScope, expand
from wio.rules.inputs import build_rule_catalog
lazy from wio.models.rule import LoadedRuleset, Rule

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.models.config import Config
    from wio.models.rules import Routes
    from wio.rules.expansion import Expansion

type OriginLayer = Literal["root", "stage", "always-include"]
"""The three layers that include, in the order that origins are sorted."""


@dataclass(frozen=True)
class Origin:
    """One include entry of the config that delivers a rule.

    It is immutable and hashable.

    Attributes:
        layer: The layer of the entry.
        name: The name of the root or of the stage, and `None` for
            `rules_always_include`.
        routes: Every route of the expansion that led from the entry to the
            rule, sorted, with canonical ruleset names only.
    """

    layer: OriginLayer
    name: str | None
    routes: Routes


@dataclass(frozen=True)
class SelectedAnywhere:
    """Which rules some include entry delivers, and which an exclude took out.

    It is immutable and hashable when its mappings are frozen, as
    `selected_anywhere` builds them. Both are in the order of C-2 of `wio rules`.

    Attributes:
        selected: Each rule that some entry delivers, with an origin for each
            layer and name that does, in the order root, stage, always-include
            and then by name. A rule that is not a key is selected by no entry.
        removed: Each rule that the exclude of a rule preset took out of an
            entry, with the origins of those entries; a rule can be in both
            mappings when another entry delivers it.
    """

    selected: Mapping[Rule, tuple[Origin, ...]]
    removed: Mapping[Rule, tuple[Origin, ...]]


def selected_anywhere(
    config: Config, rulesets: Mapping[str, LoadedRuleset]
) -> SelectedAnywhere:
    """Find the rules that any include entry of the config delivers.

    The entries are the rule presets of each root, the `rules_include` of each
    stage and `rules_always_include`, each expanded by `expand` over the catalog
    of `build_rule_catalog`. An entry counts whatever the roots, and the
    excludes of a stage and the always excludes leave a rule selected, because
    they remove it from a view and do not unselect it. An entry or part of it
    that cannot be expanded delivers nothing and raises nothing.

    It does no input or output, and the result does not depend on the order of
    the tables of the config or of the entries of its lists.

    Args:
        config: The settings, whose roots, stages and always includes are read.
        rulesets: The rulesets by canonical name, as `ruleset_map` gives them.

    Returns:
        The rules delivered and the rules taken out, each with its origins.
    """
    catalog = build_rule_catalog(config, rulesets)
    found = [
        (entry, expand(entry.references, [], ConfigScope(), catalog))
        for entry in _entries(config)
    ]
    return _collect(found)


@dataclass(frozen=True)
class _Entry:
    """The references of one layer and name, as written in the config."""

    layer: OriginLayer
    name: str | None
    references: tuple[str, ...]

    def sort_name(self) -> str:
        """Give the name that the entries of one layer are sorted by.

        Returns:
            The name of the root or of the stage.
        """
        return self.name or ""


def _entries(config: Config) -> list[_Entry]:
    """List the include entries of the config."""
    roots = [_Entry("root", n, r.rule_presets) for n, r in config.roots.items()]
    stages = [_Entry("stage", n, s.rules_include) for n, s in config.stages.items()]
    always = _Entry("always-include", None, config.rules_always_include)
    return [
        *sorted(roots, key=_Entry.sort_name),
        *sorted(stages, key=_Entry.sort_name),
        always,
    ]


def _collect(found: Sequence[tuple[_Entry, Expansion]]) -> SelectedAnywhere:
    """Gather the expansions of the entries into the rules and their origins."""
    chosen: dict[Rule, list[Origin]] = {}
    taken: dict[Rule, list[Origin]] = {}
    for entry, expansion in found:
        for target, rules in ((chosen, expansion.rules), (taken, expansion.removed)):
            for rule, routes in rules.items():
                target.setdefault(rule, []).append(
                    Origin(entry.layer, entry.name, routes)
                )
    return SelectedAnywhere(_in_order(chosen), _in_order(taken))


def _in_order(found: dict[Rule, list[Origin]]) -> Mapping[Rule, tuple[Origin, ...]]:
    """Put rules in the order of C-2 of `wio rules` and freeze the mapping."""
    order = sorted(found, key=lambda r: (r.ruleset, r.family, r.number, r.code))
    return freeze({rule: tuple(found[rule]) for rule in order})
