# SPDX-License-Identifier: Apache-2.0
"""How the rules that apply are grouped by the roots they apply to."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.models.config import Root
    from wio.models.rule import Rule
    from wio.models.rules import Selection


@dataclass(frozen=True)
class RuleGroup:
    """The rules that apply to one exact set of roots.

    Attributes:
        line: The line that introduces the group, which names the roots and
            their paths, or says that the rules are for every root.
        rules: The rules of the group, in the order the selection gives them.
    """

    line: str
    rules: tuple[Rule, ...]


def group_rules(
    selection: Selection, roots: Mapping[str, Root]
) -> tuple[RuleGroup, ...]:
    """Group the included rules of a selection by their exact set of roots.

    A rule that the selection leaves out is in no group, and an included rule is
    in exactly one. The rules that need no root come first, under
    `Rules for every root:`. The other groups follow in the order of their root
    names compared one by one, a shorter list before a longer one that it
    begins, so the order of the config never changes the result. Their lines are
    `Rules for root <name> (<paths>):` for one root and
    `Rules for roots <name>, <name> (<paths>):` for several, with the paths in
    the order of the root names and, within a root, of the config.

    Args:
        selection: The rules with their decisions, whose included rules name the
            roots that reach them, none for a root-independent one.
        roots: The roots of the config by name, which gives their paths.

    Returns:
        The groups, none for a selection that includes no rule.
    """
    del selection, roots
    raise NotImplementedError
