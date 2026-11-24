# SPDX-License-Identifier: Apache-2.0
"""The types of the listing that `wio rules list` prints.

A `Listing` is built by `wio.rules` and rendered by it, and the leaves that
narrow or explain it fill the fields that are left empty here, so the field sets
are part of the contract between those leaves.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.models.rule import Rule
    from wio.models.rules import Decision, Routes


class Explanation(Protocol):
    """What a listing says about where a rule came from.

    The renderer prints it without knowing what it holds: the lines under the
    rule's block, and the fields in the rule's JSON object.
    """

    def lines(self) -> tuple[str, ...]:
        """Write the explanation for a person.

        Returns:
            The detail lines to print under the block, none ended by a newline.
        """
        ...

    def fields(self) -> Mapping[str, object]:
        """Write the explanation for a program.

        Returns:
            The keys and JSON-ready values to add after the fields of the rule.
        """
        ...


@dataclass(frozen=True)
class Header:
    """Which view a listing is and what was applied to it.

    Attributes:
        view: What was asked for, such as `every rule`, `root api`,
            `file src/api/app.py`, `Work W` or `stage s`.
        work: The id of the Work whose roots were taken, if any.
        layers: The names of the layers applied, `roots`, `stage` and
            `always fields`, in that order; empty when none was applied.
        roots: The roots that applied, empty when none did, or `None` when the
            roots were not applied.
        stage: The name of the stage given, if any.
        references: The references that narrowed the listing, as typed.
        not_selected: Whether the listing holds the rules that nothing selects.
    """

    view: str
    work: str | None
    layers: tuple[str, ...]
    roots: tuple[str, ...] | None
    stage: str | None
    references: tuple[str, ...]
    not_selected: bool


@dataclass(frozen=True)
class Row:
    """One rule considered by a listing.

    Attributes:
        rule: The rule.
        decision: What the selection decided, or `None` when no layer was
            applied and nothing was decided.
        via: The routes by which the rule was reached, filled when the listing
            is narrowed by references.
        explanation: The explanation that a row asks to be shown with, if any.
    """

    rule: Rule
    decision: Decision | None
    via: Routes
    explanation: Explanation | None


@dataclass(frozen=True)
class Listing:
    """The rules that a view considers, with the header that describes it.

    Attributes:
        header: The view and what was applied.
        rows: Every rule considered, in the order of C-2 of `wio rules`; which
            are shown is the renderer's decision.
    """

    header: Header
    rows: tuple[Row, ...]
