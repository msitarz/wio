# SPDX-License-Identifier: Apache-2.0
"""The decision of every rule: included with its roots, or out with its reason.

The layers say which rules are selected, and this module says where each applies:
a selected rule applies when its ruleset is root-independent or reached by a
selected root. One `select` serves every view of a listing and every consumer of
a selection. It reads no file.
"""

from typing import TYPE_CHECKING

from wio.models.frozen import freeze
from wio.models.rules import Decision, Reason
from wio.rules.layers import apply_layers

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping

    from wio.models.config import Config
    from wio.models.rule import LoadedRuleset, Rule
    from wio.models.rules import LayerEffect, Selection
    from wio.rules.layers import RuleLayers


def select(
    roots: tuple[str, ...] | None,
    stage: str | None,
    config: Config,
    rulesets: Mapping[str, LoadedRuleset],
) -> Selection:
    """Decide every rule of every ruleset for the roots and the stage.

    Raises:
        KeyError: A name of `roots` or `stage` is not in the config, as
            `apply_layers` raises it.
    """
    layered = apply_layers(roots, stage, config, rulesets)
    given = None if roots is None else frozenset(roots)
    candidates = sorted(config.roots if given is None else given)
    decisions = {
        rule: _decide(rule, layers, config, layered.reach, candidates, applied=given)
        for rule, layers in layered.rules.items()
    }
    return freeze(decisions)


def _decide(
    rule: Rule,
    layers: RuleLayers,
    config: Config,
    reach: Mapping[str, frozenset[str]],
    candidates: list[str],
    *,
    applied: Collection[str] | None,
) -> Decision:
    """Decide one rule."""
    table = config.rulesets.get(rule.ruleset)
    independent = table is not None and table.root_independent
    effects = layers.effects
    if not layers.selected:
        return Decision(
            included=False,
            roots=(),
            root_independent=independent,
            effects=effects,
            reason=_removal(effects),
        )
    reaching = () if independent else _reaching(rule, reach, candidates)
    cut = applied is not None and not independent and not reaching
    return Decision(
        included=not cut,
        roots=reaching,
        root_independent=independent,
        effects=effects,
        reason=Reason("cut-by-roots", None) if cut else None,
    )


def _reaching(
    rule: Rule, reach: Mapping[str, frozenset[str]], candidates: list[str]
) -> tuple[str, ...]:
    """List the roots among the candidates that reach a rule's ruleset."""
    return tuple(name for name in candidates if rule.ruleset in reach[name])


def _removal(effects: tuple[LayerEffect, ...]) -> Reason:
    """Give the reason that a rule the layers did not select is out."""
    for effect in reversed(effects):
        if effect.action != "removes":
            continue
        match effect.layer:
            case "always-exclude":
                return Reason("vetoed", None)
            case "root" | "stage" as layer:
                return Reason("excluded", layer)
            case "always-include":
                continue
    return Reason("not-selected", None)
