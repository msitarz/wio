# SPDX-License-Identifier: Apache-2.0
"""The order of the rules of a group and the lines that introduce families."""

from itertools import groupby
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from wio.context.ports import Topics
    from wio.models.rule import Rule


def order_rules(rules: Iterable[Rule], topics: Topics) -> tuple[str | Rule, ...]:
    """Put the rules of one group in order, with a line before each family.

    The order is by the name of the ruleset, then by family, then by the number
    of the code and then its text, so it depends on the names alone: not on the
    order given, and not on how a rule was selected, which a rule does not carry.

    Args:
        rules: The rules of one group, in any order.
        topics: Gives the topic of each family.

    Returns:
        The rules in order, and before the first rule of each family of each
        ruleset the line `<ruleset>: <topic> (<FAMILY>)`, once; nothing for no
        rule.

    Raises:
        KeyError: If `topics` has no topic for a family of a rule.
    """
    items: list[str | Rule] = []
    ordered = sorted(rules, key=lambda r: (r.ruleset, r.family, r.number, r.code))
    for (ruleset, family), members in groupby(
        ordered, key=lambda r: (r.ruleset, r.family)
    ):
        items.append(f"{ruleset}: {topics.topic(ruleset, family)} ({family})")
        items.extend(members)
    return tuple(items)
