# SPDX-License-Identifier: Apache-2.0
"""The four layers that select the rules of a stage, applied in their order.

The layers are the rule presets of the roots, the rules of the stage, and the
two always fields of the config. Each is expanded by `wio.rules.expand` and
applied to the set that the layers before it built, and every rule keeps what
each layer did to it, so a listing can say why a rule is in or out. The module
reads no file. Cutting a rule by the roots that apply, and the `Decision` of a
rule, are built on its result elsewhere.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.models.config import Config
    from wio.models.rule import LoadedRuleset, Rule
    from wio.models.rules import LayerEffect
    from wio.rules.expansion import Problem


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

    A layer is applied only when its input is given: the root layer for the
    roots, the stage layer for the stage, and the two always fields in every
    call. A layer works on the set that the layers before it built. The roots
    add together, in the order of their names; the stage adds its includes and
    then removes what its excludes name; the always includes add over any earlier
    exclude; and the always excludes remove last, over the always includes. An
    exclude records an effect for every rule it names, whether or not the rule
    was in the set. An exclude inside the rule preset that an include entry names
    takes rules out of that entry's includes only: it records a `removes` effect
    in the layer of the entry and unselects nothing that another entry or layer
    added. Every reference is expanded by `expand` over the catalog that
    `build_rule_catalog` gives, and a reference that cannot be expanded is a
    problem of the result that selects nothing.

    It does no input or output, and the result does not depend on the order of
    the tables of the config, of the entries of a list or of `roots`.

    Args:
        roots: The names of the roots that the stage selects, or `None` for none.
        stage: The name of the stage, or `None` for none.
        config: The settings, whose roots, stages and always fields are read.
        rulesets: The rulesets by canonical name, as `ruleset_map` gives them.

    Returns:
        The rules with their effects, the rulesets that each root of the config
        reaches whether or not it was given, so a call for no roots and no stage
        still has them, and the problems of the expansions that were applied. A
        problem that two expansions share, such as a bad entry of a rule preset
        that two roots include, is listed once.

    Raises:
        KeyError: A name of `roots` is not a root of the config, or `stage` is not
            a stage of it. It names what was not found.
    """
    del config
    msg = f"apply_layers for {roots} and {stage} over {len(rulesets)} is declared"
    raise NotImplementedError(msg)
