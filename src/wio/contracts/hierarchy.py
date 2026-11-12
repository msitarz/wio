# SPDX-License-Identifier: Apache-2.0
"""The hierarchy and the dependency graph of the Works of a project."""

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.models.diagnostics import Diagnostic, order_diagnostics
from wio.models.frozen import freeze

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from pathlib import Path

    from wio.models.config import HierarchyMode
    from wio.models.works import Work

_DESCENDANTS = "@descendants"
_LISTED = "listed in depends_on"
_CHILD = "a parent waits for its child"
type _Graph = Mapping[Path, Mapping[Path, str]]
"""The edges out of each Work by path, each with its kind, sorted by path."""


@dataclass(frozen=True)
class Hierarchy:
    """The relations between the Works that discovery found.

    It is immutable and is built once by `build_hierarchy`, so every command
    gets the same answer. Each table is keyed by the `path` of a Work, which is
    unique, because two Works may share an id. Every Work given to
    `build_hierarchy` is a key of every table, and a caller reads only those
    paths: a lookup of another path raises `KeyError`. Under `flat`, no Work has
    a parent, a child, an ancestor or a descendant.

    Attributes:
        works: The Works it was built from, sorted by the string of their paths.
        parent: The Work of the nearest directory above a Work's own that holds
            one, so a plain directory, or one whose Work was left out, is passed
            over, or `None` for a top Work.
        children: The Works whose parent a Work is, sorted by the string of their
            paths.
        ancestors: The parent, then the parent's parent and so on, nearest
            first.
        descendants: The children, their children and so on, sorted by the
            string of their paths.
        roots: A Work's own roots with `@descendants` replaced by the union of
            what its children's roots resolve to, each name once and sorted. A
            Work without children resolves `@descendants` to nothing.
        dependencies: The ids a Work lists in `depends_on`, in the order listed,
            an id that no Work has included, because the diagnostics report it.
            The implicit wait of a parent for its children is not one.
        dependents: The Works whose `depends_on` has a Work's id, sorted by the
            string of their paths. A parent that waits for the Work as its child
            is not one, and Works that share an id have the same dependents.
        diagnostics: The errors of the dependency graph, ordered by
            `order_diagnostics`: an unknown id, once for each Work and id, and
            a group of Works that wait on each other, once for each group.
    """

    works: tuple[Work, ...]
    parent: frozendict[Path, Work | None]
    children: frozendict[Path, tuple[Work, ...]]
    ancestors: frozendict[Path, tuple[Work, ...]]
    descendants: frozendict[Path, tuple[Work, ...]]
    roots: frozendict[Path, tuple[str, ...]]
    dependencies: frozendict[Path, tuple[str, ...]]
    dependents: frozendict[Path, tuple[Work, ...]]
    diagnostics: tuple[Diagnostic, ...]


def build_hierarchy(works: Sequence[Work], mode: HierarchyMode) -> Hierarchy:
    """Build the hierarchy and check the dependency graph of some Works.

    It reads no file and writes none. Under `nesting` the graph holds the listed
    edges and a parent's implicit edge to each child, under `flat` the listed
    edges only. An id that two Works share counts as existing, and a dependency
    on it is an edge to each of them.

    Every diagnostic is an error, placed at a Work's file. A dependency on an id
    that no Work has is one error for each Work and id, reading
    ``The dependency `zzzzzz` is not a Work``. A group of Works that wait on each
    other is one error at the file of its Work with the smallest path, and shows
    the shortest cycle that starts at that Work, taking among equally short ones
    the edge to the Work with the smallest path, and calling an edge listed when
    a pair has both kinds. It reads
    ``Dependency cycle: a → b (listed in depends_on) → a (a parent waits for its
    child)``, each step naming the id it reaches and the kind of its edge, and a
    Work that lists its own id is a cycle of one.

    Args:
        works: The Works that discovery found, in any order.
        mode: The hierarchy mode of the config.

    Returns:
        The hierarchy, with the diagnostics ordered by `order_diagnostics`.
    """
    ordered = tuple(sorted(works, key=lambda work: str(work.path)))
    relatives = _relatives(ordered, mode)
    edges = _listed_edges(ordered)
    return Hierarchy(
        works=ordered,
        parent=freeze(relatives.parent),
        children=freeze(relatives.children),
        ancestors=freeze(relatives.ancestors),
        descendants=freeze(relatives.descendants),
        roots=freeze(_resolve_roots(ordered, relatives.children)),
        dependencies=freeze(edges.dependencies),
        dependents=freeze(edges.dependents),
        diagnostics=order_diagnostics(_graph_errors(ordered, relatives)),
    )


@dataclass(frozen=True)
class _Relatives:
    """The relations that the layout gives, before roots and edges use them.

    Attributes:
        parent: The parent of each Work, by path.
        children: The children of each Work, by path.
        ancestors: The ancestors of each Work, nearest first, by path.
        descendants: The descendants of each Work, by path.
    """

    parent: Mapping[Path, Work | None]
    children: Mapping[Path, tuple[Work, ...]]
    ancestors: Mapping[Path, tuple[Work, ...]]
    descendants: Mapping[Path, tuple[Work, ...]]


def _relatives(works: Sequence[Work], mode: HierarchyMode) -> _Relatives:
    """Derive the parent, children, ancestors and descendants from the paths.

    Args:
        works: The Works, sorted by the string of their paths.
        mode: The hierarchy mode; under `flat` every Work has no relatives.

    Returns:
        Each table with a key for every Work.
    """
    homes = {work.path.parent: work for work in works} if mode == "nesting" else {}
    ancestors = {
        work.path: tuple(homes[d] for d in work.path.parent.parents if d in homes)
        for work in works
    }
    children = _grouped(works, lambda work: ancestors[work.path][:1])
    descendants = _grouped(works, lambda work: ancestors[work.path])
    return _Relatives(
        parent={path: above[0] if above else None for path, above in ancestors.items()},
        children=children,
        ancestors=ancestors,
        descendants=descendants,
    )


def _grouped(
    works: Sequence[Work], owners: Callable[[Work], Sequence[Work]]
) -> dict[Path, tuple[Work, ...]]:
    """Collect, for each Work, the Works that name it as an owner.

    Args:
        works: The Works, sorted by the string of their paths.
        owners: Gives the Works that a Work is collected under.

    Returns:
        For each Work, by path, those collected under it, in the order of the
        Works.
    """
    found: dict[Path, list[Work]] = {work.path: [] for work in works}
    for work in works:
        for owner in owners(work):
            found[owner.path].append(work)
    return {path: tuple(members) for path, members in found.items()}


def _resolve_roots(
    works: Sequence[Work], children: Mapping[Path, tuple[Work, ...]]
) -> dict[Path, tuple[str, ...]]:
    """Resolve `@descendants` in the roots of each Work through its children.

    Args:
        works: The Works, sorted by the string of their paths.
        children: The children of each Work, by path.

    Returns:
        The resolved roots of each Work, by path.
    """
    resolved: dict[Path, tuple[str, ...]] = {}
    for work in works:
        _roots_of(work, children, resolved)
    return resolved


def _roots_of(
    work: Work,
    children: Mapping[Path, tuple[Work, ...]],
    resolved: dict[Path, tuple[str, ...]],
) -> tuple[str, ...]:
    """Resolve the roots of one Work, and of its children as needed.

    Args:
        work: The Work.
        children: The children of each Work, by path.
        resolved: The roots resolved so far, by path, to which it adds.

    Returns:
        The Work's own entries and, when it lists `@descendants`, what each of
        its children resolves to, each name once and sorted.
    """
    if work.path not in resolved:
        kids = children[work.path] if _DESCENDANTS in work.roots else ()
        names = {root for root in work.roots if root != _DESCENDANTS}
        names.update(*(_roots_of(kid, children, resolved) for kid in kids))
        resolved[work.path] = tuple(sorted(names))
    return resolved[work.path]


@dataclass(frozen=True)
class _Edges:
    """The edges that `depends_on` lists, from both ends.

    Attributes:
        dependencies: The ids each Work lists, in the order listed, by path.
        dependents: The Works that list each Work's id, by path, each sorted by
            the string of their paths.
    """

    dependencies: Mapping[Path, tuple[str, ...]]
    dependents: Mapping[Path, tuple[Work, ...]]


def _listed_edges(works: Sequence[Work]) -> _Edges:
    """Read the dependencies and the dependents from the listed ids.

    Args:
        works: The Works, sorted by the string of their paths.

    Returns:
        The edges, with a key for every Work.
    """
    listing: dict[str, list[Work]] = defaultdict(list)
    for work in works:
        for dependency in dict.fromkeys(work.depends_on):
            listing[dependency].append(work)
    return _Edges(
        dependencies={work.path: work.depends_on for work in works},
        dependents={work.path: tuple(listing[work.id]) for work in works},
    )


def _graph_errors(works: Sequence[Work], relatives: _Relatives) -> list[Diagnostic]:
    """Find the unknown ids and the dependency cycles of the graph.

    Args:
        works: The Works, sorted by the string of their paths.
        relatives: The relations of the Works, whose children give the implicit
            edges.

    Returns:
        One error for each unknown id of each Work and one for each group of
        Works that wait on each other, in any order.
    """
    known = {work.id for work in works}
    unknown = [
        Diagnostic(
            "error", work.path.as_posix(), f"The dependency `{id_}` is not a Work"
        )
        for work in works
        for id_ in dict.fromkeys(work.depends_on)
        if id_ not in known
    ]
    return [*unknown, *_cycle_errors(works, relatives.children)]


def _cycle_errors(
    works: Sequence[Work], children: Mapping[Path, tuple[Work, ...]]
) -> list[Diagnostic]:
    """Report each group of Works that wait on each other, once.

    Args:
        works: The Works, sorted by the string of their paths.
        children: The children of each Work, by path.

    Returns:
        One error for each group, at the file of its Work with the smallest
        path, in the order of those paths.
    """
    graph = _graph(works, children)
    names = {work.path: work.id for work in works}
    return [
        Diagnostic("error", start.as_posix(), _cycle_message(start, graph, names))
        for start in _cycle_starts(graph)
    ]


def _cycle_starts(graph: _Graph) -> list[Path]:
    """Find the first Work of each group of Works that wait on each other.

    Args:
        graph: The edges.

    Returns:
        The Work with the smallest path of each group, in the order of the
        paths.
    """
    reach = {path: _reach(path, graph) for path in graph}
    return [
        path
        for path in sorted(graph, key=str)
        if path in reach[path] and _is_first(path, reach)
    ]


def _is_first(path: Path, reach: Mapping[Path, set[Path]]) -> bool:
    """Tell whether a Work on a cycle has the smallest path of its group.

    Args:
        path: A Work on a cycle.
        reach: The Works that each Work waits for, through any edges.

    Returns:
        Whether no Work that waits for it and is waited for by it has a smaller
        path.
    """
    return all(str(path) <= str(node) for node in reach[path] if path in reach[node])


def _graph(works: Sequence[Work], children: Mapping[Path, tuple[Work, ...]]) -> _Graph:
    """Build the edges of the graph.

    A parent waits for its children, and a Work for the ids it lists.

    Args:
        works: The Works, sorted by the string of their paths.
        children: The children of each Work, by path.

    Returns:
        For each Work the Works it waits for, sorted by the string of their
        paths, each with its kind. A pair with both kinds of edge is listed.
    """
    paths: dict[str, list[Path]] = defaultdict(list)
    for work in works:
        paths[work.id].append(work.path)
    graph: dict[Path, dict[Path, str]] = {}
    for work in works:
        out = {child.path: _CHILD for child in children[work.path]}
        for dependency in work.depends_on:
            out.update(dict.fromkeys(paths.get(dependency, ()), _LISTED))
        graph[work.path] = dict(sorted(out.items(), key=lambda edge: str(edge[0])))
    return graph


def _reach(start: Path, graph: _Graph) -> set[Path]:
    """Find the Works that a Work waits for, through any number of edges.

    Args:
        start: The Work.
        graph: The edges.

    Returns:
        The Works reached by one edge or more, so the start only when it is on a
        cycle.
    """
    found: set[Path] = set()
    frontier = set(graph[start])
    while frontier:
        found |= frontier
        frontier = {after for node in frontier for after in graph[node]} - found
    return found


def _cycle_message(start: Path, graph: _Graph, names: Mapping[Path, str]) -> str:
    """Write the shortest cycle through a Work.

    Args:
        start: The Work with the smallest path of its group.
        graph: The edges.
        names: The id of each Work, by path.

    Returns:
        `Dependency cycle: ` and the id of the start, then each step's id and
        the kind of its edge, joined by arrows.
    """
    distance = _distances(start, graph)
    remaining = 1 + min(distance[node] for node in graph[start] if node in distance)
    current, steps = start, [names[start]]
    while remaining:
        remaining -= 1
        step = min((n for n in graph[current] if distance.get(n) == remaining), key=str)
        steps.append(f"{names[step]} ({graph[current][step]})")
        current = step
    return "Dependency cycle: " + " → ".join(steps)


def _distances(target: Path, graph: _Graph) -> dict[Path, int]:
    """Count the edges from each Work to a Work that can reach it.

    Args:
        target: The Work to reach.
        graph: The edges.

    Returns:
        The fewest edges from each Work that reaches the target, the target
        being 0.
    """
    waiting = _waiting(graph)
    distance = {target: 0}
    queue = deque([target])
    while queue:
        node = queue.popleft()
        for source in waiting[node]:
            if source not in distance:
                distance[source] = distance[node] + 1
                queue.append(source)
    return distance


def _waiting(graph: _Graph) -> dict[Path, list[Path]]:
    """Turn the edges around.

    Args:
        graph: The edges.

    Returns:
        For each Work the Works that wait for it.
    """
    waiting: dict[Path, list[Path]] = defaultdict(list)
    for source, out in graph.items():
        for node in out:
            waiting[node].append(source)
    return waiting
