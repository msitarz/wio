# SPDX-License-Identifier: Apache-2.0
"""Tests of the decision of each rule: included with its roots, or out."""

from dataclasses import FrozenInstanceError, replace
from typing import TYPE_CHECKING

import pytest

from tests.unit.rules.support import make_ruleset
from wio.models.config import Config, Root, Ruleset, Stage
from wio.models.frozen import freeze
from wio.rules import select

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.models.rule import LoadedRuleset
    from wio.models.rules import Decision, Selection


def _rulesets(*specs: tuple[str, str, Sequence[str]]) -> Mapping[str, LoadedRuleset]:
    """Build rulesets that declare one family each.

    Args:
        *specs: A ruleset name, its family and the codes of its rules.

    Returns:
        The rulesets by name.
    """
    built = [make_ruleset(name, [family], codes) for name, family, codes in specs]
    return freeze({ruleset.name: ruleset for ruleset in built})


def _config(
    roots: Mapping[str, Sequence[str]],
    stages: Mapping[str, tuple[Sequence[str], Sequence[str]]],
    *,
    independent: Sequence[str] = (),
    include: Sequence[str] = (),
    exclude: Sequence[str] = (),
) -> Config:
    """Build a config with roots, stages, always fields and ruleset settings.

    Args:
        roots: Each root and its rule presets.
        stages: Each stage with its includes and excludes.
        independent: The rulesets whose `root_independent` is set.
        include: The `rules_always_include`.
        exclude: The `rules_always_exclude`.

    Returns:
        The config.
    """
    return Config(
        roots=freeze({n: Root(("src",), tuple(p)) for n, p in roots.items()}),
        stages=freeze(
            {
                n: Stage(goal="g", rules_include=tuple(i), rules_exclude=tuple(e))
                for n, (i, e) in stages.items()
            }
        ),
        rulesets=freeze({n: Ruleset(root_independent=True) for n in independent}),
        rules_always_include=tuple(include),
        rules_always_exclude=tuple(exclude),
    )


def _basic() -> tuple[Config, Mapping[str, LoadedRuleset]]:
    """Build the repository of AC-1.

    Returns:
        The config, where `api` reaches `demo` only and `process` is
        root-independent, and the rulesets `demo`, `web` and `process`.
    """
    rulesets = _rulesets(
        ("demo", "ARC", ["ARC001"]),
        ("web", "WEB", ["WEB001"]),
        ("process", "FIX", ["FIX001"]),
    )
    config = _config(
        {"api": ["demo.all"]},
        {"s": (["web.WEB001", "process.FIX001"], [])},
        independent=["process"],
    )
    return config, rulesets


def _of(selection: Selection, ruleset: str, code: str) -> Decision:
    """Find the decision of a rule.

    Args:
        selection: The selection.
        ruleset: The rule's ruleset.
        code: The rule's code.

    Returns:
        Its decision.
    """
    (found,) = [
        d for r, d in selection.items() if (r.ruleset, r.code) == (ruleset, code)
    ]
    return found


def _reason(decision: Decision) -> tuple[str, str | None] | None:
    """Show a decision's reason as a pair.

    Args:
        decision: The decision.

    Returns:
        The kind and the layer of its reason, or `None` for an included rule.
    """
    reason = decision.reason
    return None if reason is None else (reason.kind, reason.layer)


def test_a_selected_rule_applies_where_its_ruleset_is_reached() -> None:
    """AC-1: reached, unreached and root-independent."""
    # Given `api` reaching `demo` only, `process` root-independent, and a stage
    # that includes `web.WEB001` and `process.FIX001`
    config, rulesets = _basic()

    # When the rules are selected for `api` and `s`
    found = select(("api",), "s", config, rulesets)

    # Then `demo` applies to `api`, `web` is cut by the roots, and `process` is
    # included for every root
    arc = _of(found, "demo", "ARC001")
    assert (arc.included, arc.roots, arc.reason) == (True, ("api",), None)
    web = _of(found, "web", "WEB001")
    assert (web.included, web.roots, _reason(web)) == (
        False,
        (),
        ("cut-by-roots", None),
    )
    fix = _of(found, "process", "FIX001")
    assert (fix.included, fix.roots, fix.root_independent) == (True, (), True)


def test_a_root_independent_ruleset_that_a_root_reaches_has_no_roots() -> None:
    """AC-1: it applies to every root whether or not one reaches it."""
    # Given the same repository with `process.all` in the presets of `api`
    config, rulesets = _basic()
    config = replace(
        config, roots=freeze({"api": Root(("src",), ("demo.all", "process.all"))})
    )

    # When the rules are selected for `api` and `s`
    found = select(("api",), "s", config, rulesets)

    # Then `FIX001` is included with `root_independent` and no roots, as before
    fix = _of(found, "process", "FIX001")
    assert (fix.included, fix.roots, fix.root_independent) == (True, (), True)


def _reasons_repository() -> tuple[Config, Mapping[str, LoadedRuleset]]:
    """Build the repository of AC-2.

    Returns:
        The config and the rulesets `demo` and `web`.
    """
    demo = make_ruleset(
        "demo",
        ["ARC", "PAY"],
        ["ARC001", "ARC002", "ARC003", "PAY001", "PAY002", "PAY003"],
        {"recommended": (["ARC"], ["ARC001"])},
    )
    web = make_ruleset("web", ["WEB"], ["WEB001"])
    config = _config(
        {"api": ["demo.recommended"]},
        {
            "s": (
                ["demo.PAY001", "demo.PAY002", "web.WEB001"],
                ["demo.ARC002", "demo.ARC003"],
            )
        },
        include=["demo.ARC003"],
        exclude=["demo.PAY001"],
    )
    return config, freeze({"demo": demo, "web": web})


def test_the_reason_is_the_last_layer_that_removed_the_rule() -> None:
    """AC-2: not selected, excluded by a layer, vetoed, cut by the roots."""
    # Given a repository where each reason occurs once
    config, rulesets = _reasons_repository()

    # When the rules are selected for `api` and `s`
    found = select(("api",), "s", config, rulesets)

    # Then each out rule has its reason, and the two that came back are included
    assert _reason(_of(found, "demo", "PAY003")) == ("not-selected", None)
    assert _reason(_of(found, "demo", "ARC001")) == ("excluded", "root")
    assert _reason(_of(found, "demo", "ARC002")) == ("excluded", "stage")
    assert _reason(_of(found, "demo", "PAY001")) == ("vetoed", None)
    assert _reason(_of(found, "web", "WEB001")) == ("cut-by-roots", None)
    assert _of(found, "demo", "ARC003").included
    assert _of(found, "demo", "PAY002").included
    assert len(_of(found, "demo", "ARC003").effects) == 3
    assert _of(found, "demo", "PAY003").effects == ()


def test_the_last_layer_that_removed_a_rule_decides_the_reason() -> None:
    """A-1: stage after root, veto after stage, and an always-include nested exclude."""
    # Given `ARC001` removed by the root's rule preset and then by the stage,
    # `ARC002` removed by the stage and then vetoed, and `PAY001` that only the
    # exclude of a rule preset of the always includes removed
    demo = make_ruleset(
        "demo",
        ["ARC", "PAY"],
        ["ARC001", "ARC002", "PAY001", "PAY002"],
        {
            "recommended": (["ARC"], ["ARC001"]),
            "extra": (["PAY001", "PAY002"], ["PAY001"]),
        },
    )
    config = _config(
        {"api": ["demo.recommended"]},
        {"s": ([], ["demo.ARC001", "demo.ARC002"])},
        include=["demo.extra"],
        exclude=["demo.ARC002"],
    )

    # When the rules are selected for `api` and `s`
    found = select(("api",), "s", config, freeze({"demo": demo}))

    # Then each reason is that of the last layer that removed the rule, and the
    # nested exclude of the always includes gives none
    assert _reason(_of(found, "demo", "ARC001")) == ("excluded", "stage")
    assert _reason(_of(found, "demo", "ARC002")) == ("vetoed", None)
    assert _reason(_of(found, "demo", "PAY001")) == ("not-selected", None)
    assert _of(found, "demo", "PAY002").roots == ("api",)


def test_without_roots_nothing_is_cut_and_a_rule_lists_the_roots_that_reach_it() -> (
    None
):
    """AC-3: the roots are not applied."""
    # Given the repository of AC-1 with a second root `ui` and `demo.ARC001` also
    # included by the stage
    config, rulesets = _basic()
    config = replace(
        config,
        roots=freeze({"api": Root(("src",), ("demo.all",)), "ui": Root(("src",), ())}),
        stages=freeze(
            {
                "s": Stage(
                    goal="g",
                    rules_include=("demo.ARC001", "web.WEB001", "process.FIX001"),
                )
            }
        ),
    )

    # When the rules are selected for no roots and `s`, and for no roots and no stage
    with_stage = select(None, "s", config, rulesets)
    neither = select(None, None, config, rulesets)

    # Then `ARC001` lists the root `api`, `WEB001` has no root, `FIX001` is
    # root-independent, and nothing is cut by the roots; with no stage only the
    # always fields apply, so nothing the stage selects is included
    arc = _of(with_stage, "demo", "ARC001")
    assert (arc.included, arc.roots) == (True, ("api",))
    web = _of(with_stage, "web", "WEB001")
    assert (web.included, web.roots) == (True, ())
    fix = _of(with_stage, "process", "FIX001")
    assert (fix.included, fix.root_independent) == (True, True)
    for found in (with_stage, neither):
        assert all(
            d.reason is None or d.reason.kind != "cut-by-roots" for d in found.values()
        )
    assert not any(d.included for d in neither.values())


def _shared(*, reverse: bool = False) -> tuple[Config, Mapping[str, LoadedRuleset]]:
    """Build the repository of AC-4, declared in one order or the reverse.

    Args:
        reverse: Whether to declare the rulesets, the roots and their entries in
            the reverse order.

    Returns:
        The config, where `api` reaches `demo` and `shared` and `ui` reaches
        those and `only`, and the three rulesets.
    """
    specs = [
        ("demo", "ARC", ["ARC001"]),
        ("shared", "SHR", ["SHR001"]),
        ("only", "ONE", ["ONE001"]),
    ]
    api = ["demo.all", "shared.all"]
    ui = ["demo.all", "shared.all", "only.all"]
    roots = {"api": api, "ui": ui}
    if reverse:
        specs.reverse()
        roots = {"ui": ui[::-1], "api": api[::-1]}
    return _config(roots, {}), _rulesets(*specs)


def test_a_rule_that_several_selected_roots_reach_applies_to_all_of_them() -> None:
    """AC-4: in the order of the root names."""
    # Given `api` reaching `demo` and `shared`, and `ui` reaching those and `only`
    config, rulesets = _shared()

    # When the rules are selected for the roots `("ui", "api")`
    found = select(("ui", "api"), None, config, rulesets)

    # Then `demo` and `shared` apply to `("api", "ui")` and `only` to `("ui",)`
    assert _of(found, "demo", "ARC001").roots == ("api", "ui")
    assert _of(found, "shared", "SHR001").roots == ("api", "ui")
    assert _of(found, "only", "ONE001").roots == ("ui",)


def test_no_roots_at_all_leaves_only_the_root_independent_rules() -> None:
    """AC-5: an empty tuple applies the roots and none is given."""
    # Given the repository of AC-1
    config, rulesets = _basic()

    # When the rules are selected for the roots `()` and `s`
    found = select((), "s", config, rulesets)

    # Then `FIX001` is included, `WEB001` is cut by the roots and `ARC001` is not
    # selected, because no root layer applied
    assert _of(found, "process", "FIX001").included
    assert _reason(_of(found, "web", "WEB001")) == ("cut-by-roots", None)
    assert _reason(_of(found, "demo", "ARC001")) == ("not-selected", None)


def test_the_selection_holds_every_rule_once_and_is_a_value() -> None:
    """AC-6: C-2 order, equal for equal inputs, frozen."""
    # Given rules in two rulesets and two families
    config, rulesets = _reasons_repository()

    # When the rules are selected twice
    first = select(("api",), "s", config, rulesets)
    second = select(("api",), "s", config, rulesets)

    # Then there is one entry for each rule in the order of C-2, the two
    # selections are equal, and a decision cannot be assigned
    keys = [(r.ruleset, r.family, r.number, r.code) for r in first]
    assert len(keys) == 7
    assert keys == sorted(keys)
    assert first == second
    assert hash(_of(first, "demo", "ARC001")) == hash(_of(second, "demo", "ARC001"))
    with pytest.raises(FrozenInstanceError):
        _of(first, "demo", "ARC001").included = True  # type: ignore[misc]


def test_an_unknown_stage_or_root_is_not_caught() -> None:
    """AC-7: the `KeyError` of the layers."""
    # Given the repository of AC-1
    config, rulesets = _basic()

    # When the rules are selected for an unknown stage and for an unknown root
    # Then each raises `KeyError` naming it
    with pytest.raises(KeyError, match="none"):
        select(("api",), "none", config, rulesets)
    with pytest.raises(KeyError, match="none"):
        select(("none",), "s", config, rulesets)


def test_the_selection_does_not_depend_on_the_order_of_the_inputs() -> None:
    """AC-8: the tables, the entries and the roots in two orders."""
    # Given the repository of AC-4 declared in two orders
    config, rulesets = _shared()
    reordered, backwards = _shared(reverse=True)

    # When the rules are selected for each order of the roots
    first = select(("ui", "api"), None, config, rulesets)
    second = select(("api", "ui"), None, reordered, backwards)

    # Then the selections are equal, rule by rule and in order
    assert first == second
    assert list(first.items()) == list(second.items())
