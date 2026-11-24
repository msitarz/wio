# SPDX-License-Identifier: Apache-2.0
"""The cycles of a graph of names, found once for every component that needs them.

`wio.config` finds the cycles of `after` and of the config's rule presets, and
`wio.rules` finds those of a manifest's, and neither may import the other, so the
search lives here, and so does what the two share about rule presets: which names
make an edge, where a cycle is reported and how it is worded.
"""

from typing import TYPE_CHECKING

lazy from wio.formats.wording import and_list

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.models.config import RulePreset


def find_cycles(after: Mapping[str, Sequence[str]]) -> tuple[tuple[str, ...], ...]:
    """Find the cycles of a graph by a depth-first search.

    Args:
        after: Each action's name mapped to the names it comes after. A name
            that is not a key has no edges, and an edge to it ends the search.

    Returns:
        One sorted tuple of names for each strongly connected component that has
        a cycle, a self loop included, and the tuples sorted by first name.
    """
    reach = {name: _reachable(after, name) for name in after}
    groups = {
        tuple(sorted(other for other in reach[name] if name in reach.get(other, ())))
        for name in after
        if name in reach[name]
    }
    return tuple(sorted(groups))


def _reachable(graph: Mapping[str, Sequence[str]], start: str) -> set[str]:
    """Find the names that a name reaches by one edge or more.

    Args:
        graph: Each name mapped to the names it has an edge to.
        start: The name to start from.

    Returns:
        The names reached, `start` among them only when it lies on a cycle.
    """
    seen: set[str] = set()
    stack = list(graph[start])
    while stack:
        name = stack.pop()
        if name not in seen:
            seen.add(name)
            stack.extend(graph.get(name, ()))
    return seen


def rule_preset_cycles(
    presets: Mapping[str, RulePreset],
) -> tuple[tuple[str, ...], ...]:
    """Find the cycles of a set of rule presets.

    An edge is an entry of `rules_include` or of `rules_exclude` that is the bare
    name of a rule preset of the set, because the expansion reads an exclude as a
    list too, and one that closes a cycle cannot be expanded.

    Args:
        presets: The rule presets by name, without `all`, which is the whole
            ruleset and no rule preset.

    Returns:
        The cycles as `find_cycles` gives them.
    """
    graph = {
        name: [
            e for e in (*preset.rules_include, *preset.rules_exclude) if e in presets
        ]
        for name, preset in presets.items()
    }
    return find_cycles(graph)


def cycle_key(first: RulePreset, cycle: Sequence[str]) -> str:
    """Say which list of the first member of a cycle the error is reported at.

    Args:
        first: The first member of the cycle by name.
        cycle: The members, sorted.

    Returns:
        `rules_include` when one of its includes names a member, and
        `rules_exclude` otherwise, because then an exclude closes the cycle.
    """
    named = any(entry in cycle for entry in first.rules_include)
    return "rules_include" if named else "rules_exclude"


def cycle_message(cycle: Sequence[str]) -> str:
    """Word the error of one cycle of rule presets.

    Args:
        cycle: The members, sorted.

    Returns:
        The sentence, in the singular for a rule preset that names itself.
    """
    names = and_list([f"`{name}`" for name in cycle])
    phrase = "name one another" if len(cycle) > 1 else "names itself"
    return f"{names} {phrase}; a rule preset cannot reach itself."
