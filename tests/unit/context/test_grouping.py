# SPDX-License-Identifier: Apache-2.0
"""Tests of the grouping of the rules that apply by their roots."""

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

import pytest

from wio.context.grouping import group_rules
from wio.models.config import Root
from wio.models.rule import Rule
from wio.models.rules import Decision, Reason

if TYPE_CHECKING:
    from wio.context.grouping import RuleGroup
    from wio.models.rules import ReasonKind, Selection

_PENDING = pytest.mark.xfail(strict=True, raises=NotImplementedError)
_API = Root(paths=("services/api",))
_WEB = Root(paths=("apps/web", "apps/admin"))
_ROOTS = {"api": _API, "web": _WEB}
_EVERY = "Rules for every root:"
_ONLY_API = "Rules for root api (services/api):"
_BOTH = "Rules for roots api, web (services/api, apps/web, apps/admin):"
_ONLY_WEB = "Rules for root web (apps/web, apps/admin):"


def _rule(code: str) -> Rule:
    """Build a rule that its code tells apart.

    Args:
        code: The code.

    Returns:
        The rule.
    """
    path = PurePosixPath(f"{code}.md")
    return Rule("demo", code, "a-rule", None, "", "", 1, path)


def _in(*roots: str) -> Decision:
    """Decide that a rule applies to roots.

    Args:
        *roots: The roots, none for a root-independent rule.

    Returns:
        The decision.
    """
    return Decision(
        included=True,
        roots=roots,
        root_independent=not roots,
        effects=(),
        reason=None,
    )


def _out(kind: ReasonKind, *, root_independent: bool = False) -> Decision:
    """Decide that a rule does not apply.

    Args:
        kind: Why it is out.
        root_independent: The setting of its ruleset.

    Returns:
        The decision.
    """
    return Decision(
        included=False,
        roots=(),
        root_independent=root_independent,
        effects=(),
        reason=Reason(kind, "stage" if kind == "excluded" else None),
    )


def _shown(groups: tuple[RuleGroup, ...]) -> list[tuple[str, list[str]]]:
    """Reduce groups to their lines and codes, without the order inside one.

    Args:
        groups: The groups.

    Returns:
        Each line with its codes, sorted.
    """
    return [(g.line, sorted(r.code for r in g.rules)) for g in groups]


@_PENDING
def test_the_rules_that_need_no_root_come_first() -> None:
    """AC-1: under one line, ahead of a root given before them."""
    # Given a selection with a rule of `api` and then a root-independent rule
    selection: Selection = {_rule("API001"): _in("api"), _rule("FIX001"): _in()}

    # When the groups are built
    found = _shown(group_rules(selection, _ROOTS))

    # Then the rules for every root come first
    assert found == [(_EVERY, ["FIX001"]), (_ONLY_API, ["API001"])]


@_PENDING
def test_there_is_no_every_root_line_without_such_rules() -> None:
    """AC-1: no empty group."""
    # Given a selection with a rule of `api` only
    selection: Selection = {_rule("API001"): _in("api")}

    # When the groups are built
    found = _shown(group_rules(selection, _ROOTS))

    # Then there is one group, for `api`
    assert found == [(_ONLY_API, ["API001"])]


@_PENDING
@pytest.mark.parametrize(
    "roots",
    [_ROOTS, {"web": _WEB, "api": _API}],
    ids=["api-first", "web-first"],
)
def test_a_group_is_the_exact_set_of_roots_in_the_order_of_their_names(
    roots: dict[str, Root],
) -> None:
    """AC-2, AC-3: three groups, sorted, whatever the order of the config."""
    # Given rules of `web`, of both and of `api`, mixed, and a config in either
    # order whose `web` has two paths that do not sort in their order
    selection: Selection = {
        _rule("WEB001"): _in("web"),
        _rule("BOT001"): _in("api", "web"),
        _rule("API001"): _in("api"),
        _rule("WEB002"): _in("web"),
        _rule("BOT002"): _in("api", "web"),
    }

    # When the groups are built
    found = _shown(group_rules(selection, roots))

    # Then each rule is in the group of its exact roots, sorted by their names
    assert found == [
        (_ONLY_API, ["API001"]),
        (_BOTH, ["BOT001", "BOT002"]),
        (_ONLY_WEB, ["WEB001", "WEB002"]),
    ]


@_PENDING
def test_groups_are_ordered_by_names_one_by_one() -> None:
    """AC-3: a shorter list comes before a longer one that it begins."""
    # Given roots `a`, `ab` and `b`, and rules of `ab`, of `a` and `b`, and of `a`
    roots = {name: Root(paths=(f"p/{name}",)) for name in ("a", "ab", "b")}
    selection: Selection = {
        _rule("X001"): _in("ab"),
        _rule("Y001"): _in("a", "b"),
        _rule("Z001"): _in("a"),
    }

    # When the groups are built
    lines = [group.line for group in group_rules(selection, roots)]

    # Then `a` is first, then `a, b`, then `ab`
    assert lines == [
        "Rules for root a (p/a):",
        "Rules for roots a, b (p/a, p/b):",
        "Rules for root ab (p/ab):",
    ]


@_PENDING
def test_only_the_rules_that_apply_are_grouped() -> None:
    """AC-4: four ways out are in no group."""
    # Given one rule of each way out, some of them root-independent, and none in
    outside: Selection = {
        _rule("OUT001"): _out("excluded"),
        _rule("OUT002"): _out("vetoed", root_independent=True),
        _rule("OUT003"): _out("cut-by-roots"),
        _rule("OUT004"): _out("not-selected", root_independent=True),
    }

    # When the groups are built without and then with one included rule
    without = group_rules(outside, _ROOTS)
    with_one = _shown(group_rules({**outside, _rule("IN001"): _in("api")}, _ROOTS))

    # Then there is no group, and then one that holds the included rule only
    assert without == ()
    assert with_one == [(_ONLY_API, ["IN001"])]
