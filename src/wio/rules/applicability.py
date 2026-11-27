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

    It applies the layers with `apply_layers` and then decides each rule. The
    roots are applied when `roots` is not `None`, an empty tuple included; then
    a selected rule is included when its ruleset is root-independent or reached
    by a selected root, with those roots in the order of their names, and is out
    as `cut-by-roots` otherwise. When the roots are not applied, no rule is cut,
    and a rule that is not root-independent lists the roots of the config that
    reach its ruleset, in the order of their names. A rule of a root-independent
    ruleset applies to every root, so it has no roots and `root_independent`
    true, whether or not a root also reaches its ruleset. A rule that the layers
    did not select is out with the reason of the last layer that removed it:
    `excluded` for a root or the stage, including the exclude of a rule preset
    that an entry of that layer names, `vetoed` for the always excludes, and
    `not-selected` when no layer touched it. The exclude of a rule preset inside
    an entry of the always includes took nothing out of the set, so it gives no
    reason: a rule that only it removed is `not-selected`. A rule that a layer
    removed is never reported as cut by the roots.

    It does no input or output, and the result does not depend on the order of
    the tables of the config, of the entries of its lists or of `roots`.

    Args:
        roots: The roots to apply, which `None` leaves unapplied.
        stage: The stage to apply, or `None` for no stage.
        config: The settings: the roots, the stages, the always fields and what
            each ruleset is set to.
        rulesets: Every ruleset of the repository by its canonical name, in the
            form that `ruleset_map` gives.

    Returns:
        One decision for each rule of every ruleset, in the order of C-2 of
        `wio rules`.

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
