# SPDX-License-Identifier: Apache-2.0
"""The cycles of a graph of names, found once for every component that needs them.

`wio.config` finds the cycles of `after` and of the config's rule presets, and
`wio.rules` finds those of a manifest's, and neither may import the other, so the
search lives here.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


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
