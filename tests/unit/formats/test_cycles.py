# SPDX-License-Identifier: Apache-2.0
"""Tests of the cycles of a graph of names."""

import pytest

from wio.formats import find_cycles


@pytest.mark.parametrize(
    ("graph", "cycles"),
    [
        ({"a": (), "b": ("a",)}, ()),
        ({"a": ("b",), "b": ("a",)}, (("a", "b"),)),
        (
            {"a": ("b",), "b": ("a",), "c": ("d",), "d": ("c",)},
            (("a", "b"), ("c", "d")),
        ),
        ({"a": ("b", "c"), "b": ("a",), "c": ("a",)}, (("a", "b", "c"),)),
        ({"a": ("a",)}, (("a",),)),
        ({"a": ("zzz",), "b": ("a",)}, ()),
        ({"a": ("b",), "b": ("a",), "c": ("a",)}, (("a", "b"),)),
    ],
    ids=[
        "no edges",
        "one cycle",
        "two cycles",
        "shared name",
        "self loop",
        "unknown name",
        "path into a cycle",
    ],
)
def test_find_cycles_gives_each_cycle_once_from_its_least_name(
    graph: dict[str, tuple[str, ...]], cycles: tuple[tuple[str, ...], ...]
) -> None:
    """AC-3: a cycle is reported once, however many actions reach it."""
    # Given the graph of `after` edges

    # When its cycles are found
    found = find_cycles(graph)

    # Then each strongly connected cycle is one tuple of sorted names, and the
    # tuples are sorted
    assert found == cycles
