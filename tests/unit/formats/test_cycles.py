# SPDX-License-Identifier: Apache-2.0
"""Tests of the cycles of a graph of names."""

import pytest

from wio.formats import cycle_key, cycle_message, find_cycles, rule_preset_cycles
from wio.models.config import RulePreset


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


def test_an_include_or_an_exclude_that_names_a_rule_preset_is_an_edge() -> None:
    """Both lists make edges, and a qualified name or `all` does not."""
    # Given `a` that includes `b`, `b` that excludes `c`, `c` that includes `a` and
    # a qualified name, and `d` that names a qualified name and `all` only
    presets = {
        "a": RulePreset(rules_include=("b",)),
        "b": RulePreset(rules_exclude=("c",)),
        "c": RulePreset(rules_include=("a", "docs.d")),
        "d": RulePreset(rules_include=("docs.a", "all")),
    }

    # When the cycles of the rule presets are found
    found = rule_preset_cycles(presets)

    # Then `a`, `b` and `c` are one cycle and `d` is none
    assert found == (("a", "b", "c"),)


@pytest.mark.parametrize(
    ("first", "key"),
    [
        (RulePreset(rules_include=("b",)), "rules_include"),
        (
            RulePreset(rules_include=("docs.all",), rules_exclude=("b",)),
            "rules_exclude",
        ),
        (RulePreset(rules_exclude=("b",)), "rules_exclude"),
    ],
    ids=["include", "qualified include", "exclude only"],
)
def test_a_cycle_is_reported_at_the_include_that_names_a_member_else_the_exclude(
    first: RulePreset, key: str
) -> None:
    """The key is `rules_include` only when one of its includes names a member."""
    # Given the first member of a cycle of `a` and `b`
    # When the key of the report is chosen
    found = cycle_key(first, ("a", "b"))

    # Then it is the include that names a member, and the exclude otherwise
    assert found == key


def test_the_message_names_the_members_and_a_self_loop_is_singular() -> None:
    """One sentence for several rule presets, and one for a rule preset itself."""
    # Given a cycle of two and a cycle of one
    # When each is worded
    two = cycle_message(("a", "b"))
    one = cycle_message(("s",))

    # Then the first says the two name one another and the second that it names
    # itself
    assert two == "`a` and `b` name one another; a rule preset cannot reach itself."
    assert one == "`s` names itself; a rule preset cannot reach itself."
