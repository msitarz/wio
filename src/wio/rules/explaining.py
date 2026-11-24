# SPDX-License-Identifier: Apache-2.0
"""Explaining a listing: where each rule came from and why a rule is out."""

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final

lazy from wio.models.listing import Listing
lazy from wio.models.rules import Reason
lazy from wio.rules.inputs import chain_labels, chain_text, layer_label

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from wio.models.listing import Header, Row
    from wio.models.rules import Layer, LayerEffect, Route
    from wio.rules.anywhere import Origin, SelectedAnywhere

type Chain = tuple[str, ...]
"""The labels that say where a rule came from, or what removed it: a layer
label, when there is one, and then the route from the outermost rule preset to
the entry that named the rule."""


_RANK: Final[Mapping[Layer, int]] = {
    "root": 0,
    "stage": 1,
    "always-include": 2,
    "always-exclude": 3,
}
"""The order of the layers in which origins and removals are sorted."""


@dataclass(frozen=True)
class RuleExplanation:
    """Why one rule is in a listing or out of it.

    It satisfies the `Explanation` protocol of `wio.models.listing`, so the
    renderer prints it without knowing how it was made. It is immutable and
    hashable.

    Attributes:
        code: The rule's qualified code, which every chain of the text starts
            with.
        origins: The chains of the layers and routes that selected the rule, in
            the order of layer, name and route, or the routes of the references
            for a listing with no layers.
        reason: Why the rule is out, or `None` when it is included or there is
            nothing to say.
        removed_by: The chains of what removed the rule, in the same order.
    """

    code: str
    origins: tuple[Chain, ...]
    reason: Reason | None
    removed_by: tuple[Chain, ...]

    def lines(self) -> tuple[str, ...]:
        """Write the explanation for a person.

        Returns:
            One `from:` line for each origin, then the `out:` line when the rule
            is out, then one `by:` line for each chain that removed it. A line
            writes a chain with the rule's code first and the labels joined by
            `←`; there is no line for what there is nothing to say about.
        """
        lines = [f"from: {chain_text(self.code, c)}" for c in self.origins]
        if self.reason is not None:
            lines.append(f"out: {_reason_text(self.reason)}")
        lines.extend(f"by: {chain_text(self.code, c)}" for c in self.removed_by)
        return tuple(lines)

    def fields(self) -> Mapping[str, object]:
        """Write the explanation for a program.

        Returns:
            `origins` and `removed_by` as arrays of arrays of labels, without the
            code, and `reason` as an object with `kind` and `layer`, or `null`.
        """
        reason = self.reason
        return {
            "origins": [list(chain) for chain in self.origins],
            "reason": None
            if reason is None
            else {"kind": reason.kind, "layer": reason.layer},
            "removed_by": [list(chain) for chain in self.removed_by],
        }


def _reason_text(reason: Reason) -> str:
    """Write the reason a rule is out.

    Args:
        reason: The reason of the decision.

    Returns:
        `not selected`, `excluded by the root's rule preset`,
        `excluded by the stage`, `vetoed by rules_always_exclude` or
        `cut by the roots`.
    """
    match reason.kind, reason.layer:
        case "not-selected", _:
            return "not selected"
        case "excluded", "root":
            return "excluded by the root's rule preset"
        case "excluded", _:
            return "excluded by the stage"
        case "vetoed", _:
            return "vetoed by rules_always_exclude"
        case _:
            return "cut by the roots"


def explain(listing: Listing, anywhere: SelectedAnywhere) -> Listing:
    """Give every row of a listing the explanation of its rule.

    In a layered listing the layers explain a row from its decision, and the
    routes of any references are ignored: each `adds` effect is an origin, each
    `removes` effect a removal, and the reason is the decision's. In a listing
    with no layers the routes that the references delivered the rule by are its
    origins; a row that `--not-selected` shows has the reason `not selected`,
    and what an exclude of a rule preset removed from an include entry, which
    `anywhere` records, removes it. The stage a label names is the header's. It
    does no input or output and keeps the rows and the header as they are.

    Args:
        listing: The listing, narrowed or not.
        anywhere: The rules that some include entry delivers and what the
            excludes of rule presets removed, which the caller computes once for
            the repository.

    Returns:
        The listing with an explanation on every row.
    """
    rows = tuple(_explained(row, listing.header, anywhere) for row in listing.rows)
    return Listing(listing.header, rows)


def _explained(row: Row, header: Header, anywhere: SelectedAnywhere) -> Row:
    """Give one row the explanation of its rule.

    Args:
        row: The row.
        header: The header of the listing, whose stage names the stage's label.
        anywhere: What the excludes of rule presets removed.

    Returns:
        The row with its explanation.
    """
    code = row.rule.qualified
    decision = row.decision
    if decision is not None:
        adds = _chains(decision.effects, "adds", header.stage)
        removes = _chains(decision.effects, "removes", header.stage)
        return replace(
            row, explanation=RuleExplanation(code, adds, decision.reason, removes)
        )
    origins = tuple(chain_labels(None, route) for route in sorted(row.via))
    if not header.not_selected:
        return replace(row, explanation=RuleExplanation(code, origins, None, ()))
    removed = _removals(anywhere.removed.get(row.rule, ()))
    reason = Reason("not-selected", None)
    return replace(row, explanation=RuleExplanation(code, origins, reason, removed))


def _chains(
    effects: Iterable[LayerEffect], action: str, stage: str | None
) -> tuple[Chain, ...]:
    """Write the chains of what the layers added or removed.

    Args:
        effects: What each layer did to the rule.
        action: `adds` or `removes`.
        stage: The name of the stage, which an effect of the stage layer does not
            hold.

    Returns:
        One chain for each route of each effect, sorted by layer, then name, then
        route.
    """
    found = [
        (e.layer, e.root if e.layer == "root" else stage, route)
        for e in effects
        if e.action == action
        for route in e.routes
    ]
    return _sorted(found)


def _removals(origins: Iterable[Origin]) -> tuple[Chain, ...]:
    """Write the chains of what excludes of rule presets removed.

    Args:
        origins: The include entries that an exclude took the rule out of.

    Returns:
        One chain for each route of each origin, sorted as `_chains` sorts.
    """
    return _sorted([(o.layer, o.name, r) for o in origins for r in o.routes])


def _sorted(found: Iterable[tuple[Layer, str | None, Route]]) -> tuple[Chain, ...]:
    """Sort and write the chains of layers, names and routes.

    Args:
        found: A layer, the name of its root or stage, and a route, for each chain.

    Returns:
        The chains, in the order of layer, name and route.
    """
    ordered = sorted(found, key=lambda f: (_RANK[f[0]], f[1] or "", f[2]))
    return tuple(chain_labels(layer_label(f[0], f[1]), f[2]) for f in ordered)
