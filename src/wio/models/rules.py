# SPDX-License-Identifier: Apache-2.0
"""The types for the selection of rules for a stage, and the routes it records.

`Decision` is declared by the Work that implements `wio rules list`, which fills
in its fields; until then it has none. A `Route` is here and not in `wio.rules`
because a `Decision` holds routes and a model may not import a component.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.models.rule import Rule

type Route = tuple[str, ...]
"""How a rule was reached: the canonical references from the outermost rule
preset to the entry that named it, such as
`("backend", "demo.recommended", "demo.ARC")`. The route of a removal ends with
the exclude entry. A reference names its ruleset by its canonical name, never by
an alias."""

type Routes = tuple[Route, ...]
"""Every route of one rule, sorted."""


type Layer = Literal["root", "stage", "always-include", "always-exclude"]
"""The four layers that select rules, in the order they apply."""

type EffectAction = Literal["adds", "removes"]
"""What a layer did to a rule: put it in the set, or took it out."""


@dataclass(frozen=True)
class LayerEffect:
    """What one layer did to one rule, and by which routes.

    It is immutable and hashable, and a `Decision` holds it.

    Attributes:
        layer: The layer that acted.
        action: `adds` when an include of the layer selected the rule, and
            `removes` when an exclude named it, or when the exclude of a rule
            preset that an include entry named took it out of that entry's
            includes.
        root: The name of the root, for the `root` layer, and `None` for the
            others.
        routes: The routes of `wio.rules.expand` that led to the rule, sorted.
    """

    layer: Layer
    action: EffectAction
    root: str | None
    routes: Routes


type ReasonKind = Literal["not-selected", "excluded", "vetoed", "cut-by-roots"]
"""Why a rule is out: no layer touched it, a root or stage layer removed it, an
always exclude removed it, or the layers kept it and the roots cut it."""


@dataclass(frozen=True)
class Reason:
    """Why one rule is out of a selection.

    It is immutable and hashable.

    Attributes:
        kind: `not-selected` when no layer touched the rule, `excluded` when the
            last layer that removed it is a root or the stage, `vetoed` when it
            is `rules_always_exclude`, and `cut-by-roots` when the layers kept
            the rule and the roots that apply do not reach its ruleset.
        layer: For `excluded`, the layer that removed it, `root` or `stage`;
            `None` for the others.
    """

    kind: ReasonKind
    layer: Literal["root", "stage"] | None


@dataclass(frozen=True)
class Decision:
    """Whether one rule applies to a Work at a stage, and why.

    It is immutable and hashable, so a selection can be compared and a decision
    can be a key.

    Attributes:
        included: Whether the rule applies.
        roots: For an included rule that is not root-independent, the selected
            roots that reach its ruleset in the order of their names, or the
            roots of the config that reach it when the roots are not applied;
            empty for a rule that is out and for a root-independent one.
        root_independent: The setting of the rule's ruleset in the config, for
            every rule, included or out.
        effects: What each layer did to the rule, in the order the layers
            applied, as `wio.rules.apply_layers` records it.
        reason: Why the rule is out, `None` for an included rule.
    """

    included: bool
    roots: tuple[str, ...]
    root_independent: bool
    effects: tuple[LayerEffect, ...]
    reason: Reason | None


type Selection = Mapping[Rule, Decision]
"""Every rule considered for a stage, in a fixed order, with its decision."""
