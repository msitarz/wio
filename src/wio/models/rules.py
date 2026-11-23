# SPDX-License-Identifier: Apache-2.0
"""The types for the selection of rules for a stage, and the routes it records.

`Decision` is declared by the Work that implements `wio rules list`, which fills
in its fields; until then it has none. A `Route` is here and not in `wio.rules`
because a `Decision` holds routes and a model may not import a component.
"""

from typing import TYPE_CHECKING

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


class Decision:
    """Whether one rule applies to a Work at a stage, and why.

    For an included rule it holds the roots the rule applies to, which group
    the rules in a bundle, and the layers that selected it; for an excluded
    one, the reason it was left out (excluded by a layer, vetoed by
    `rules_always_exclude`, or cut by roots), which `wio rules list --explain`
    shows.
    """


type Selection = Mapping[Rule, Decision]
"""Every rule considered for a stage, in a fixed order, with its decision."""
