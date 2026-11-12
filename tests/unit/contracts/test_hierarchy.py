# SPDX-License-Identifier: Apache-2.0
"""Tests of the hierarchy and the dependency graph of the Works."""

from pathlib import Path
from typing import TYPE_CHECKING, Literal

from wio.contracts.hierarchy import build_hierarchy
from wio.models.frozen import freeze
from wio.models.works import Work

if TYPE_CHECKING:
    from collections.abc import Iterable


def _work(
    directory: str,
    work_id: str | None = None,
    roots: tuple[str, ...] = (),
    depends_on: tuple[str, ...] = (),
) -> Work:
    """Build a Work that sits at `<directory>/README.md`.

    Args:
        directory: The Work's directory.
        work_id: The Work's id; the last part of the directory when not given.
        roots: The roots it lists.
        depends_on: The ids it lists.

    Returns:
        The Work.
    """
    return Work(
        id=work_id or Path(directory).name,
        title=None,
        path=Path(directory) / "README.md",
        template=None,
        roots=roots,
        depends_on=depends_on,
        actions=freeze({}),
    )


def _ids(works: Iterable[Work | None]) -> list[str]:
    """List the ids of some Works.

    Args:
        works: The Works, or `None` for none.

    Returns:
        Their ids, in order, with `-` for `None`.
    """
    return ["-" if work is None else work.id for work in works]


def _at(directory: str) -> Path:
    """Give the key of a Work in the tables of a hierarchy, which is its path.

    Args:
        directory: The Work's directory.

    Returns:
        The path of its file.
    """
    return Path(directory) / "README.md"


def _tree() -> list[Work]:
    """Build the Works of the first scenario of AC-1.

    Returns:
        `p`, `p/c1`, `p/c1/d`, `p/g/x` and `q`, given out of order.
    """
    return [
        _work("q"),
        _work("p/g/x"),
        _work("p"),
        _work("p/c1/d"),
        _work("p/c1"),
    ]


def test_the_parent_is_the_nearest_directory_above_that_holds_a_work() -> None:
    """A plain directory is passed over, and the relations follow the parents."""
    # Given Works in a tree where `p/g` holds no Work
    works = _tree()

    # When the hierarchy is built under nesting
    found = build_hierarchy(works, "nesting")

    # Then the parents, children, ancestors and descendants are those of the tree
    # in the order of the paths, and a leaf has no children
    assert [_ids([found.parent[w.path]])[0] for w in found.works] == [
        "-",  # p
        "p",  # p/c1
        "c1",  # p/c1/d
        "p",  # p/g/x
        "-",  # q
    ]
    path = _at("p")
    assert _ids(found.children[path]) == ["c1", "x"]
    assert _ids(found.ancestors[_at("p/c1/d")]) == ["c1", "p"]
    assert _ids(found.descendants[path]) == ["c1", "d", "x"]
    assert found.children[_at("p/c1/d")] == ()
    assert found.diagnostics == ()


def test_a_directory_whose_work_was_left_out_is_passed_over() -> None:
    """A Work below a directory that holds no Work has the Work above as parent."""
    # Given a Work `p` and a Work `k` below `p/m`, which holds no Work
    works = [_work("p"), _work("p/m/k")]

    # When the hierarchy is built under nesting
    found = build_hierarchy(works, "nesting")

    # Then the parent of `k` is `p`
    assert _ids([found.parent[_at("p/m/k")]]) == ["p"]


def test_under_flat_nobody_is_related_and_descendants_resolves_to_nothing() -> None:
    """Under flat no Work has a relative, and the graph has the listed edges."""
    # Given the Works of the first scenario with `p` listing `@descendants` and
    # `wio`, and `d` listing `p`
    works = [
        _work("p", roots=("@descendants", "wio")),
        _work("p/c1"),
        _work("p/c1/d", depends_on=("p",)),
        _work("p/g/x"),
        _work("q"),
    ]

    # When the hierarchy is built under flat
    found = build_hierarchy(works, "flat")

    # Then no Work has a parent, a child, an ancestor or a descendant, `p` has
    # `wio` only, `d` has the dependency `p` and nothing is reported
    for work in found.works:
        assert found.parent[work.path] is None
        assert found.children[work.path] == ()
        assert found.ancestors[work.path] == ()
        assert found.descendants[work.path] == ()
    assert found.roots[_at("p")] == ("wio",)
    assert found.dependencies[_at("p/c1/d")] == ("p",)
    assert found.diagnostics == ()


def _roots_tree(mid: tuple[str, ...]) -> list[Work]:
    """Build the Works of the first scenario of AC-3.

    Args:
        mid: The roots of `top/mid`.

    Returns:
        The Works, with `top/bad` having none.
    """
    return [
        _work("top", roots=("e2e", "@descendants")),
        _work("top/mid", roots=mid),
        _work("top/mid/deep", roots=("web",)),
        _work("top/leaf", roots=("db", "db")),
        _work("top/bad"),
        _work("solo", roots=("@descendants", "wio")),
    ]


def test_roots_resolve_through_the_children_into_one_sorted_set() -> None:
    """`@descendants` is the union of what the children's roots resolve to."""
    # Given a tree whose middle parent lists `api` only
    works = _roots_tree(("api",))

    # When the hierarchy is built under nesting
    found = build_hierarchy(works, "nesting")

    # Then each Work has its resolved roots, each name once and sorted
    resolved = {w.id: found.roots[w.path] for w in found.works}
    assert resolved == {
        "top": ("api", "db", "e2e"),
        "mid": ("api",),
        "deep": ("web",),
        "leaf": ("db",),
        "bad": (),
        "solo": ("wio",),
    }


def test_a_middle_parent_passes_up_what_its_own_roots_resolve_to() -> None:
    """A child contributes what its own roots resolve to, not what it lists."""
    # Given the same tree with the middle parent listing `@descendants`
    works = _roots_tree(("@descendants",))

    # When the hierarchy is built under nesting
    found = build_hierarchy(works, "nesting")

    # Then `mid` has `web`, and `top` has `db`, `e2e` and `web`
    assert found.roots[_at("top/mid")] == ("web",)
    assert found.roots[_at("top")] == ("db", "e2e", "web")


def test_dependents_are_the_works_that_list_the_id_and_a_parent_is_not_one() -> None:
    """The dependencies are the listed ids, and the parent's wait is implicit."""
    # Given Works `a` and `d` that list `b`, `a` also listing `c`, and `b` as
    # the child of `p`
    works = [
        _work("a", "aaaaaa", depends_on=("bbbbbb", "cccccc")),
        _work("d", "dddddd", depends_on=("bbbbbb",)),
        _work("c", "cccccc"),
        _work("p", "pppppp"),
        _work("p/b", "bbbbbb"),
    ]

    # When the hierarchy is built under nesting
    found = build_hierarchy(works, "nesting")

    # Then `b` has the dependents `a` and `d` in the order of their paths, `a`
    # has the dependencies in the order listed, and `p` is not a dependent
    assert _ids(found.dependents[_at("p/b")]) == ["aaaaaa", "dddddd"]
    assert found.dependencies[_at("a")] == ("bbbbbb", "cccccc")
    assert found.dependents[_at("p")] == ()
    assert found.diagnostics == ()


def test_an_unknown_id_is_one_error_for_each_work_and_id_a_shared_id_is_known() -> None:
    """A dependency on an id with no Work is reported, and one on a shared id is not."""
    # Given Works that list ids that no Work has, one that lists a shared id, and
    # two Works that share it
    works = [
        _work("u1", depends_on=("zzzzzz",)),
        _work("u2", depends_on=("zzzzzz",)),
        _work("u3", depends_on=("zzzzzz", "yyyyyy", "zzzzzz")),
        _work("r", depends_on=("k3m9xq",)),
        _work("s1", "k3m9xq"),
        _work("s2", "k3m9xq"),
    ]

    # When the hierarchy is built under nesting
    found = build_hierarchy(works, "nesting")

    # Then each Work and id gives one error at its file, none for `r`, and the
    # dependents of both sharing Works include `r`
    assert [(d.severity, d.where, d.message) for d in found.diagnostics] == [
        ("error", "u1/README.md", "The dependency `zzzzzz` is not a Work"),
        ("error", "u2/README.md", "The dependency `zzzzzz` is not a Work"),
        ("error", "u3/README.md", "The dependency `yyyyyy` is not a Work"),
        ("error", "u3/README.md", "The dependency `zzzzzz` is not a Work"),
    ]
    assert _ids(found.dependents[_at("s1")]) == ["r"]
    assert _ids(found.dependents[_at("s2")]) == ["r"]


def _messages(
    works: list[Work], mode: Literal["flat", "nesting"]
) -> list[tuple[str, str]]:
    """Build a hierarchy and list its diagnostics.

    Args:
        works: The Works.
        mode: `flat` or `nesting`.

    Returns:
        The place and the message of each diagnostic, in order.
    """
    found = build_hierarchy(works, mode)
    return [(d.where, d.message) for d in found.diagnostics]


def test_a_cycle_of_a_parent_that_lists_its_child_calls_the_edge_listed() -> None:
    """A pair with a listed and an implicit edge has a listed edge."""
    # Given a parent that lists its child, which lists the parent
    works = [
        _work("p", "p5n2hv", depends_on=("k3m9xq",)),
        _work("p/k", "k3m9xq", depends_on=("p5n2hv",)),
    ]

    # When the hierarchy is built under nesting
    found = _messages(works, "nesting")

    # Then the one error reads both edges as listed
    assert found == [
        (
            "p/README.md",
            (
                "Dependency cycle: p5n2hv → k3m9xq (listed in depends_on) → p5n2hv "
                "(listed in depends_on)"
            ),
        )
    ]


def test_a_cycle_through_a_parent_names_the_implicit_edge() -> None:
    """The edge from a parent to its child is one the parent waits on."""
    # Given a parent and a child that lists the parent
    works = [
        _work("p", "p5n2hv"),
        _work("p/k", "k3m9xq", depends_on=("p5n2hv",)),
    ]

    # When the hierarchy is built under nesting
    found = _messages(works, "nesting")

    # Then the one error names the implicit edge
    assert found == [
        (
            "p/README.md",
            (
                "Dependency cycle: p5n2hv → k3m9xq (a parent waits for its child) → "
                "p5n2hv (listed in depends_on)"
            ),
        )
    ]


def test_overlapping_cycles_are_one_error_and_a_self_dependency_is_a_cycle() -> None:
    """A group is one error with the shortest cycle through its first Work."""
    # Given a Work that two others wait on and wait for, and a Work that lists
    # its own id
    works = [
        _work("a", "a7b2c4", depends_on=("c9d4e6", "b8c3d5")),
        _work("b", "c9d4e6", depends_on=("a7b2c4",)),
        _work("c", "b8c3d5", depends_on=("a7b2c4",)),
        _work("s", "s5t3wx", depends_on=("s5t3wx",)),
    ]

    # When the hierarchy is built under flat
    found = _messages(works, "flat")

    # Then there is one error for the group, through the smaller path, and one
    # for the Work that waits for itself
    assert found == [
        (
            "a/README.md",
            (
                "Dependency cycle: a7b2c4 → c9d4e6 (listed in depends_on) → a7b2c4 "
                "(listed in depends_on)"
            ),
        ),
        (
            "s/README.md",
            "Dependency cycle: s5t3wx → s5t3wx (listed in depends_on)",
        ),
    ]


def test_two_separate_cycles_are_two_errors_in_order() -> None:
    """Each group is reported once, at its own first file."""
    # Given two pairs of Works that list each other
    works = [
        _work("w", "t1v2w3", depends_on=("w4x5y6",)),
        _work("t", "w4x5y6", depends_on=("t1v2w3",)),
        _work("f", "e1f2g3", depends_on=("f4g5h6",)),
        _work("e", "f4g5h6", depends_on=("e1f2g3",)),
    ]

    # When the hierarchy is built under flat
    found = _messages(works, "flat")

    # Then there are two errors in the order of their files
    assert [(where, message[:25]) for where, message in found] == [
        ("e/README.md", "Dependency cycle: f4g5h6 "),
        ("t/README.md", "Dependency cycle: w4x5y6 "),
    ]


def test_a_longer_cycle_is_found_through_the_smallest_paths() -> None:
    """The shortest cycle is taken, and ties go to the smaller path."""
    # Given a chain of three Works that wait for the next and a shortcut that
    # leaves the first for the last
    works = [
        _work("a", "aaaaaa", depends_on=("bbbbbb", "cccccc")),
        _work("b", "bbbbbb", depends_on=("cccccc",)),
        _work("c", "cccccc", depends_on=("aaaaaa",)),
    ]

    # When the hierarchy is built under flat
    found = _messages(works, "flat")

    # Then the cycle takes the shortcut, and no second error is reported
    assert found == [
        (
            "a/README.md",
            (
                "Dependency cycle: aaaaaa → cccccc (listed in depends_on) → aaaaaa "
                "(listed in depends_on)"
            ),
        )
    ]
