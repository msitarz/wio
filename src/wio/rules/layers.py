# SPDX-License-Identifier: Apache-2.0
"""The four layers that select the rules of a stage, applied in their order.

The layers are the rule presets of the roots, the rules of the stage, and the
two always fields of the config. Each is expanded by `wio.rules.expand` and
applied to the set that the layers before it built, and every rule keeps what
each layer did to it, so a listing can say why a rule is in or out. The module
reads no file. Cutting a rule by the roots that apply, and the `Decision` of a
rule, are built on its result elsewhere.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from wio.models.frozen import freeze
from wio.models.rules import LayerEffect
from wio.rules.expansion import ConfigScope, Expansion, Problem, expand
from wio.rules.inputs import build_rule_catalog

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.models.config import Config
    from wio.models.rule import LoadedRuleset, Rule
    from wio.models.rules import Layer
    from wio.rules.expansion import RuleCatalog


@dataclass(frozen=True)
class RuleLayers:
    """What the layers did to one rule.

    Attributes:
        selected: Whether the rule is in the set after the last layer.
        effects: What each layer did to it, in the order the layers applied: the
            root layer by root name, then the stage, the always includes and the
            always excludes. Inside one root, and inside the stage, the adds of
            an expansion come before its removes.
    """

    selected: bool
    effects: tuple[LayerEffect, ...]


@dataclass(frozen=True)
class Layered:
    """The result of applying the layers.

    It is immutable and hashable when its mappings are frozen, as `apply_layers`
    builds them.

    Attributes:
        rules: Every rule of every ruleset, in the order of ruleset name, family,
            number and code, each with what the layers did to it; a rule that no
            layer named is present, not selected and without an effect.
        reach: For every root of the config, whether or not it was given, the
            canonical names of the rulesets that the include entries of its rule
            presets name, even when its excludes leave none of their rules.
        problems: The problems of the expansions that were applied, sorted as
            `wio.rules.expand` sorts them; a root that was not given contributes
            none, although its `reach` is returned.
    """

    rules: Mapping[Rule, RuleLayers]
    reach: Mapping[str, frozenset[str]]
    problems: tuple[Problem, ...]


def apply_layers(
    roots: tuple[str, ...] | None,
    stage: str | None,
    config: Config,
    rulesets: Mapping[str, LoadedRuleset],
) -> Layered:
    """Apply the four layers in their order to the rulesets.

    Raises:
        KeyError: A name of `roots` is not a root of the config, or `stage` is not
            a stage of it. It names what was not found.
    """
    _check_names(roots, stage, config)
    catalog = build_rule_catalog(config, rulesets)
    expansions = {
        name: expand(root.rule_presets, [], ConfigScope(), catalog)
        for name, root in sorted(config.roots.items())
    }
    state = _State()
    for name in sorted(set(roots or ())):
        state.include("root", name, expansions[name])
    if stage is not None:
        named = config.stages[stage]
        state.include("stage", None, _expand(named.rules_include, catalog))
        state.exclude("stage", _expand(named.rules_exclude, catalog))
    state.include("always-include", None, _expand(config.rules_always_include, catalog))
    state.exclude("always-exclude", _expand(config.rules_always_exclude, catalog))
    return Layered(
        rules=state.result(_ordered(rulesets)),
        reach=freeze({name: frozenset(e.rulesets) for name, e in expansions.items()}),
        problems=state.problems(),
    )


def _check_names(
    roots: tuple[str, ...] | None, stage: str | None, config: Config
) -> None:
    """Refuse a root or a stage that the config does not have."""
    for name in roots or ():
        if name not in config.roots:
            raise KeyError(name)
    if stage is not None and stage not in config.stages:
        raise KeyError(stage)


def _expand(entries: Sequence[str], catalog: RuleCatalog) -> Expansion:
    """Expand a list of entries as includes, in the config's scope."""
    return expand(entries, [], ConfigScope(), catalog)


def _ordered(rulesets: Mapping[str, LoadedRuleset]) -> list[Rule]:
    """List every rule of every ruleset in the order of C-2 of `wio rules`."""
    rules = [rule for ruleset in rulesets.values() for rule in ruleset.rules]
    return sorted(rules, key=lambda r: (r.ruleset, r.family, r.number, r.code))


@dataclass
class _State:
    """The set that the layers build, and what each layer did to each rule."""

    chosen: set[Rule] = field(default_factory=set)
    effects: dict[Rule, list[LayerEffect]] = field(default_factory=dict)
    found: set[Problem] = field(default_factory=set)

    def _note(self, rule: Rule, effect: LayerEffect) -> None:
        """Record what a layer did to a rule."""
        self.effects.setdefault(rule, []).append(effect)

    def include(self, layer: Layer, root: str | None, found: Expansion) -> None:
        """Apply the includes of a layer: add what they select, record removals.

        Args:
            layer: The layer.
            root: The root's name for the root layer, else `None`.
            found: The expansion of its includes.
        """
        for rule, routes in found.rules.items():
            self._note(rule, LayerEffect(layer, "adds", root, routes))
            self.chosen.add(rule)
        for rule, routes in found.removed.items():
            self._note(rule, LayerEffect(layer, "removes", root, routes))
        self.found.update(found.problems)

    def exclude(self, layer: Layer, found: Expansion) -> None:
        """Apply the excludes of a layer: take out and record every rule named.

        Args:
            layer: The layer.
            found: The expansion of its excludes, read as the rules they name.
        """
        for rule, routes in found.rules.items():
            self._note(rule, LayerEffect(layer, "removes", None, routes))
            self.chosen.discard(rule)
        self.found.update(found.problems)

    def result(self, rules: list[Rule]) -> Mapping[Rule, RuleLayers]:
        """Give what the layers did to every rule.

        Args:
            rules: Every rule, in the order to list them.

        Returns:
            A frozen mapping from each rule to whether it is selected and its
            effects in the order the layers applied.
        """
        return freeze(
            {
                rule: RuleLayers(rule in self.chosen, tuple(self.effects.get(rule, ())))
                for rule in rules
            }
        )

    def problems(self) -> tuple[Problem, ...]:
        """Give the problems of the expansions, each once.

        Returns:
            The problems sorted by route, reference and kind.
        """
        return tuple(sorted(self.found, key=lambda p: (p.route, p.reference, p.kind)))
