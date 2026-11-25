# SPDX-License-Identifier: Apache-2.0
"""The rules section: the rules that apply to a stage, as a session reads them."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.context.grouping import group_rules
from wio.context.ordering import order_rules
from wio.context.rendering import join_items, render_rule

if TYPE_CHECKING:
    from wio.context.ports import Topics
    from wio.models.rules import Selection
    from wio.ports import Settings


@dataclass(frozen=True)
class RulesSection:
    """The text of the rules section and the rules it holds.

    Attributes:
        text: The section without a label, empty when no rule is included.
        codes: The qualified codes of the rules in the text, in the order the
            text prints them.
    """

    text: str
    codes: tuple[str, ...]


def rules_section(
    selection: Selection, settings: Settings, topics: Topics
) -> RulesSection:
    """Print the rules that apply, grouped by their roots and in a fixed order.

    The groups and their lines are those of `group_rules`, the order and the
    family lines of each group those of `order_rules`, each rule is written by
    `render_rule`, and every line and rule is joined by `join_items` with the
    configured separator. A rule that the selection leaves out shows nowhere.

    Args:
        selection: The rules with their decisions.
        settings: Gives the paths of the roots and the separator.
        topics: Gives the topic of each family.

    Returns:
        The section and the codes of its rules.

    Raises:
        ConfigurationError: If the settings cannot be loaded.
        KeyError: If an included rule names a root that the config does not
            hold, or `topics` has no topic for its family.
    """
    config = settings.load()
    items = [
        item
        for group in group_rules(selection, config.roots)
        for item in (group.line, *order_rules(group.rules, topics))
    ]
    texts = [item if isinstance(item, str) else render_rule(item) for item in items]
    return RulesSection(
        join_items(texts, config.bundle.separator),
        tuple(item.qualified for item in items if not isinstance(item, str)),
    )
