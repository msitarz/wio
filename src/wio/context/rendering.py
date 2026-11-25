# SPDX-License-Identifier: Apache-2.0
"""How the rules section writes a rule and joins its items."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.models.rule import Rule


def render_rule(rule: Rule) -> str:
    """Write one rule as a session reads and cites it.

    It depends on the rule alone, so it cannot say why the rule was selected,
    and a selection that is reorganised without changing a rule gives the same
    text.

    Args:
        rule: The rule, whose `ruleset` is the canonical name of its ruleset.

    Returns:
        The qualified code and the name on one line, then a newline and the body
        as the rule holds it. A rule with an empty body is its line alone, with
        no newline after it.
    """
    del rule
    raise NotImplementedError


def join_items(items: Sequence[str], separator: str) -> str:
    """Join the group lines, family lines and rules of the rules section.

    Args:
        items: The items in the order the section shows them.
        separator: The configured text between two items.

    Returns:
        The items with `separator`, as written, between every two adjacent ones
        and neither before the first nor after the last; empty for no item.
    """
    del items, separator
    raise NotImplementedError
