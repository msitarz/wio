# SPDX-License-Identifier: Apache-2.0
"""Explaining a listing: where each rule came from and why a rule is out."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.models.listing import Listing
    from wio.models.rules import Reason
    from wio.rules.anywhere import SelectedAnywhere

type Chain = tuple[str, ...]
"""The labels that say where a rule came from, or what removed it: a layer
label, when there is one, and then the route from the outermost rule preset to
the entry that named the rule."""


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
        raise NotImplementedError

    def fields(self) -> Mapping[str, object]:
        """Write the explanation for a program.

        Returns:
            `origins` and `removed_by` as arrays of arrays of labels, without the
            code, and `reason` as an object with `kind` and `layer`, or `null`.
        """
        raise NotImplementedError


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
    del listing, anywhere
    raise NotImplementedError
