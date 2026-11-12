# SPDX-License-Identifier: Apache-2.0
"""Tests of how the hierarchy of the Works is composed from its leaves."""

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock

from wio.contracts import hierarchy as module
from wio.models.diagnostics import Diagnostic
from wio.models.frozen import freeze
from wio.models.works import Work

if TYPE_CHECKING:
    import pytest


def _work(name: str, depends_on: tuple[str, ...] = ()) -> Work:
    """Build a Work for a directory.

    Args:
        name: The directory's name, which is also the Work's id.
        depends_on: The ids it lists.

    Returns:
        A Work at `<name>/README.md`.
    """
    return Work(
        id=name,
        title=None,
        path=Path(name) / "README.md",
        template=None,
        roots=(),
        depends_on=depends_on,
        actions=freeze({}),
    )


def test_the_hierarchy_is_assembled_from_the_leaves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The relations, roots, dependents and errors of the leaves become one value."""
    # Given Works given out of order, and leaves that give a relation table, the
    # roots, the dependents and two errors out of order
    b, a = _work("b", ("a",)), _work("a")
    relatives = module._Relatives(  # noqa: SLF001
        parent={a.path: None, b.path: a},
        children={a.path: (b,), b.path: ()},
        ancestors={a.path: (), b.path: (a,)},
        descendants={a.path: (b,), b.path: ()},
    )
    find_relatives = Mock(return_value=relatives)
    monkeypatch.setattr(module, "_relatives", find_relatives)
    roots = {a.path: ("x",), b.path: ()}
    resolve = Mock(return_value=roots)
    monkeypatch.setattr(module, "_resolve_roots", resolve)
    dependents = {a.path: (b,), b.path: ()}
    edges = module._Edges({a.path: (), b.path: ("a",)}, dependents)  # noqa: SLF001
    find_edges = Mock(return_value=edges)
    monkeypatch.setattr(module, "_listed_edges", find_edges)
    late = Diagnostic("error", "a/README.md:12", "late")
    early = Diagnostic("error", "a/README.md:4", "early")
    judge = Mock(return_value=[late, early])
    monkeypatch.setattr(module, "_graph_errors", judge)

    # When the hierarchy is built
    found = module.build_hierarchy([b, a], "nesting")

    # Then the Works are in the order of their paths, every table is the one a
    # leaf gave, the edges are the leaf's, the errors are ordered, and
    # the leaves got the Works in order, the mode, and the relations or children
    assert found.works == (a, b)
    assert found.parent == relatives.parent
    assert found.children == relatives.children
    assert found.ancestors == relatives.ancestors
    assert found.descendants == relatives.descendants
    assert found.roots == roots
    assert found.dependents == dependents
    assert found.dependencies == edges.dependencies
    assert found.diagnostics == (early, late)
    assert find_relatives.call_args.args == ((a, b), "nesting")
    assert resolve.call_args.args == ((a, b), relatives.children)
    assert find_edges.call_args.args == ((a, b),)
    assert judge.call_args.args == ((a, b), relatives)
