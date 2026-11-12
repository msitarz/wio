# SPDX-License-Identifier: Apache-2.0
"""The hierarchy and the dependency graph of the Works of a project."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from wio.models.diagnostics import Diagnostic
    from wio.models.works import Work


@dataclass(frozen=True)
class Hierarchy:
    """The relations between the Works that discovery found.

    It is immutable and is built once by `build_hierarchy`, so every command
    gets the same answer. Each table is keyed by the `path` of a Work, which is
    unique, because two Works may share an id. Every Work given to
    `build_hierarchy` is a key of every table, and a path that is not one has no
    relations. Under `flat`, no Work has a parent, a child, an ancestor or a
    descendant.

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
        dependencies: The ids a Work lists in `depends_on` that name a Work of
            the tree, in the order listed. The implicit wait of a parent for its
            children is not one.
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
    raise NotImplementedError
