# SPDX-License-Identifier: Apache-2.0
"""The hierarchy and the dependency graph of the Works of a project."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from wio.models.diagnostics import order_diagnostics
from wio.models.frozen import freeze

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from wio.models.diagnostics import Diagnostic
    from wio.models.works import Work


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


def build_hierarchy(
    works: Sequence[Work], mode: Literal["flat", "nesting"]
) -> Hierarchy:
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


def _relatives(works: Sequence[Work], mode: Literal["flat", "nesting"]) -> _Relatives:
    """Derive the parent, children, ancestors and descendants from the paths.

    Args:
        works: The Works, sorted by the string of their paths.
        mode: The hierarchy mode; under `flat` every Work has no relatives.

    Returns:
        Each table with a key for every Work.
    """
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError
