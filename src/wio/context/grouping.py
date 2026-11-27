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

    Raises:
        KeyError: If an included rule names a root that `roots` does not hold,
            which a selection made with the same config never does.
    """
    members: dict[tuple[str, ...], list[Rule]] = {}
    for rule, decision in selection.items():
        if decision.included:
            members.setdefault(tuple(sorted(decision.roots)), []).append(rule)
    return tuple(
        RuleGroup(_line(names, roots), tuple(members[names]))
        for names in sorted(members)
    )


def _line(names: tuple[str, ...], roots: Mapping[str, Root]) -> str:
    """Write the line that introduces a group."""
    if not names:
        return "Rules for every root:"
    paths = ", ".join(path for name in names for path in roots[name].paths)
    noun = "root" if len(names) == 1 else "roots"
    shown = f" ({paths})" if paths else ""
    return f"Rules for {noun} {', '.join(names)}{shown}:"
