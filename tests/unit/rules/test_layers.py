# SPDX-License-Identifier: Apache-2.0
"""Tests of the four layers that select the rules of a stage."""

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from tests.unit.rules.support import make_ruleset
from wio.models.config import Config, Root, RulePreset, Stage
from wio.models.frozen import freeze
from wio.rules import Layered, Problem, RuleLayers, apply_layers
lazy from wio.models.rule import LoadedRuleset

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

_STUB = pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="stub")
_ALL = ("ARC001", "ARC002", "PAY001", "PAY002")


def _ruleset(
    name: str,
    codes: Sequence[str] = _ALL,
    presets: Mapping[str, tuple[Sequence[str], Sequence[str]]] | None = None,
) -> LoadedRuleset:
    """Build a ruleset that declares `ARC` and `PAY`.

    Args:
        name: The ruleset's name.
        codes: The codes of its rules.
        presets: Its rule presets, with their includes and excludes.

    Returns:
        The ruleset.
    """
    return make_ruleset(name, ["ARC", "PAY"], codes, presets)


def _demo(
    **presets: tuple[Sequence[str], Sequence[str]],
) -> Mapping[str, LoadedRuleset]:
    """Build the ruleset `demo` of AC-1 with rule presets.

    Args:
        **presets: The rule presets of its manifest, `recommended` by default.

    Returns:
        The rulesets by name.
    """
    given = presets or {"recommended": (["ARC"], [])}
    return freeze({"demo": _ruleset("demo", presets=given)})


def _config(
    *,
    roots: Mapping[str, Sequence[str]] | None = None,
    stages: Mapping[str, tuple[Sequence[str], Sequence[str]]] | None = None,
    include: Sequence[str] = ("demo.ARC001",),
    exclude: Sequence[str] = ("demo.PAY001",),
    presets: Mapping[str, RulePreset] | None = None,
) -> Config:
    """Build the config of AC-1.

    Args:
        roots: The root `api` and its rule presets, `demo.recommended` by default.
        stages: The stage `s` with its includes and excludes by default.
        include: The `rules_always_include`.
        exclude: The `rules_always_exclude`.
        presets: The config's rule presets.

    Returns:
        The config.
    """
    given_roots = roots if roots is not None else {"api": ["demo.recommended"]}
    given_stages = (
        stages if stages is not None else {"s": (["demo.PAY001"], ["demo.ARC001"])}
    )
    return Config(
        roots=freeze({n: Root(("src",), tuple(p)) for n, p in given_roots.items()}),
        stages=freeze(
            {
                n: Stage(goal="g", rules_include=tuple(i), rules_exclude=tuple(e))
                for n, (i, e) in given_stages.items()
            }
        ),
        rules_always_include=tuple(include),
        rules_always_exclude=tuple(exclude),
        rule_presets=freeze(dict(presets or {})),
    )


def _effects(
    layered: Layered, code: str, ruleset: str = "demo"
) -> list[tuple[str, str, str | None]]:
    """List what the layers did to a rule.

    Args:
        layered: The result.
        code: The rule's code.
        ruleset: The rule's ruleset.

    Returns:
        The layer, the action and the root of each effect, in order.
    """
    layers = _layers(layered, code, ruleset)
    return [(e.layer, e.action, e.root) for e in layers.effects]


def _layers(layered: Layered, code: str, ruleset: str = "demo") -> RuleLayers:
    """Find the layers of a rule.

    Args:
        layered: The result.
        code: The rule's code.
        ruleset: The rule's ruleset.

    Returns:
        What the layers did to it.
    """
    (found,) = [
        v for r, v in layered.rules.items() if (r.ruleset, r.code) == (ruleset, code)
    ]
    return found


def _selected(layered: Layered, ruleset: str = "demo") -> list[str]:
    """List the codes of the selected rules of a ruleset.

    Args:
        layered: The result.
        ruleset: The ruleset.

    Returns:
        The codes, in the order of the result.
    """
    return [
        r.code for r, v in layered.rules.items() if v.selected and r.ruleset == ruleset
    ]


@_STUB
def test_the_four_layers_apply_in_order() -> None:
    """AC-1: a rule is selected when the last layer leaves it in the set."""
    # Given the roots, the stage and the always fields of the contract
    config = _config()

    # When the layers apply for the root `api` and the stage `s`
    found = apply_layers(("api",), "s", config, _demo())

    # Then the rules are selected and recorded as the contract lists them, and all
    # four are present
    assert len(found.rules) == 4
    assert _selected(found) == ["ARC001", "ARC002"]
    assert _effects(found, "ARC001") == [
        ("root", "adds", "api"),
        ("stage", "removes", None),
        ("always-include", "adds", None),
    ]
    assert _effects(found, "ARC002") == [("root", "adds", "api")]
    assert _effects(found, "PAY001") == [
        ("stage", "adds", None),
        ("always-exclude", "removes", None),
    ]
    assert _effects(found, "PAY002") == []


@_STUB
def test_an_exclude_takes_out_what_the_layers_so_far_added() -> None:
    """AC-2: the stage's excludes remove, and the always include adds back."""
    # Given a stage `t` that includes `demo.PAY` and excludes `demo.PAY001` and
    # `demo.ARC`, and `demo.ARC002` as the only always include
    config = _config(
        stages={"t": (["demo.PAY"], ["demo.PAY001", "demo.ARC"])},
        include=["demo.ARC002"],
    )

    # When the layers apply for `api` and `t`
    found = apply_layers(("api",), "t", config, _demo())

    # Then `PAY002` and `ARC002` are selected, and `ARC002` has three effects
    assert _selected(found) == ["ARC002", "PAY002"]
    assert _effects(found, "ARC002") == [
        ("root", "adds", "api"),
        ("stage", "removes", None),
        ("always-include", "adds", None),
    ]


@_STUB
def test_the_veto_is_final_and_records_what_it_names() -> None:
    """AC-3: it wins over an always include and records a rule nothing added."""
    # Given `demo.PAY001` as both an always include and an always exclude
    both = _config(include=["demo.PAY001"], exclude=["demo.PAY001"])
    # and a veto of `demo.PAY002`, which nothing adds
    veto = _config(exclude=["demo.PAY002"])

    # When the layers apply without roots and stage, and for `api` and `s`
    first = apply_layers(None, None, both, _demo())
    second = apply_layers(("api",), "s", veto, _demo())

    # Then `PAY001` is out with both effects, and `PAY002` has the veto only
    assert "PAY001" not in _selected(first)
    assert _effects(first, "PAY001") == [
        ("always-include", "adds", None),
        ("always-exclude", "removes", None),
    ]
    assert "PAY002" not in _selected(second)
    assert _effects(second, "PAY002") == [("always-exclude", "removes", None)]


@_STUB
def test_a_layer_is_applied_only_when_its_input_is_given() -> None:
    """AC-4: no roots, no root layer; no stage, no stage layer."""
    # Given the repository of AC-1
    config = _config()

    # When the layers apply for no roots and `s`, for `api` and no stage, and for
    # neither
    no_roots = apply_layers(None, "s", config, _demo())
    no_stage = apply_layers(("api",), None, config, _demo())
    neither = apply_layers(None, None, config, _demo())

    # Then each has only the layers that its input gives, and all four rules
    layers = [
        {e.layer for v in found.rules.values() for e in v.effects}
        for found in (no_roots, no_stage, neither)
    ]
    assert layers[0] == {"stage", "always-include", "always-exclude"}
    assert layers[1] == {"root", "always-include", "always-exclude"}
    assert layers[2] == {"always-include", "always-exclude"}
    assert _effects(neither, "ARC001") == [("always-include", "adds", None)]
    assert _effects(neither, "PAY001") == [("always-exclude", "removes", None)]
    assert [len(found.rules) for found in (no_roots, no_stage, neither)] == [4, 4, 4]


def _two_roots() -> tuple[Config, Mapping[str, LoadedRuleset]]:
    """Build the repository of AC-5: `api` includes `ARC001`, `web` the family.

    Returns:
        The config and the rulesets.
    """
    rulesets = _demo(one=(["ARC001"], []), family=(["ARC"], []))
    config = _config(roots={"api": ["demo.one"], "web": ["demo.family"]})
    return config, rulesets


@_STUB
def test_several_roots_add_together_in_the_order_of_their_names() -> None:
    """AC-5: a rule that two roots add has an effect for each."""
    # Given the roots `api` with `ARC001` and `web` with the family `ARC`
    config, rulesets = _two_roots()

    # When the layers apply for the roots `("web", "api")` and no stage
    found = apply_layers(("web", "api"), None, config, rulesets)

    # Then `ARC001` has the effects of `api` and then `web`, and `ARC002` of `web`
    assert _effects(found, "ARC001")[:2] == [
        ("root", "adds", "api"),
        ("root", "adds", "web"),
    ]
    assert _effects(found, "ARC002") == [("root", "adds", "web")]


@_STUB
def test_an_exclude_of_one_root_does_not_take_out_what_another_adds() -> None:
    """AC-5: the exclude acts on the includes of its own rule preset only."""
    # Given `recommended` excluding `ARC002`, and the root `web` with the family
    rulesets = _demo(recommended=(["ARC"], ["ARC002"]), family=(["ARC"], []))
    config = _config(
        roots={"api": ["demo.recommended"], "web": ["demo.family"]},
        include=[],
        exclude=[],
    )

    # When the layers apply for `("api", "web")` and for `("web", "api")`
    first = apply_layers(("api", "web"), None, config, rulesets)
    second = apply_layers(("web", "api"), None, config, rulesets)

    # Then both agree: `ARC002` is selected, removed by `api` and added by `web`
    assert first == second
    assert "ARC002" in _selected(first)
    assert _effects(first, "ARC002") == [
        ("root", "removes", "api"),
        ("root", "adds", "web"),
    ]
    removal = _layers(first, "ARC002").effects[0]
    assert removal.routes == (("demo.recommended", "demo.ARC002"),)


def _reach_repository() -> tuple[Config, Mapping[str, LoadedRuleset]]:
    """Build the repository of AC-6.

    Returns:
        The config and the rulesets `demo`, `other` and `third`.
    """
    demo = _ruleset("demo", ["ARC001"], {"recommended": (["ARC"], ["ARC"])})
    other = _ruleset("other", ["ARC001"])
    third = _ruleset("third", ["ARC001"])
    base = RulePreset(("demo.recommended", "other.ARC"), ("third.ARC001",))
    config = _config(
        roots={"api": ["base"], "web": []},
        stages={"st": (["third.ARC"], [])},
        include=[],
        exclude=[],
        presets={"base": base},
    )
    return config, freeze({"demo": demo, "other": other, "third": third})


@_STUB
def test_the_rulesets_that_a_root_reaches_are_returned_for_every_root() -> None:
    """AC-6: even when its excludes leave none of their rules."""
    # Given `api` whose `base` includes `demo.recommended` (which excludes all of
    # `demo`) and `other.ARC` and excludes `third.ARC001`, a root `web` with none,
    # and a stage that includes `third.ARC`
    config, rulesets = _reach_repository()

    # When the layers apply for no roots and the stage, and for `api` and it
    without_roots = apply_layers(None, "st", config, rulesets)
    with_api = apply_layers(("api",), "st", config, rulesets)

    # Then `api` reaches `demo` and `other` and `web` nothing, whether or not the
    # roots were given, and `demo.ARC001` has the removal of `api` by its route
    expected = {"api": frozenset({"demo", "other"}), "web": frozenset()}
    assert dict(without_roots.reach) == expected
    assert dict(with_api.reach) == expected
    removal = [
        e
        for e in _layers(with_api, "ARC001").effects
        if (e.layer, e.action, e.root) == ("root", "removes", "api")
    ]
    assert [e.routes for e in removal] == [(("base", "demo.recommended", "demo.ARC"),)]


@_STUB
def test_an_unknown_name_is_refused_and_an_unknown_reference_is_a_problem() -> None:
    """AC-7: `KeyError` for a stage or a root, a problem for a reference."""
    # Given the repository of AC-1 and a stage `bad` with entries that cannot expand
    stages = {
        "s": (["demo.PAY001"], ["demo.ARC001"]),
        "bad": (["demo.ZZZ", "Docs"], []),
    }
    config = _config(stages=stages)
    plain = _config(stages={"bad": ([], [])})

    # When the layers apply for an unknown stage, an unknown root and `bad`
    with pytest.raises(KeyError, match="none"):
        apply_layers(("api",), "none", config, _demo())
    with pytest.raises(KeyError, match="none"):
        apply_layers(("none",), "s", config, _demo())
    found = apply_layers(("api",), "bad", config, _demo())
    baseline = apply_layers(("api",), "bad", plain, _demo())

    # Then the third has an `unknown` and a `malformed` problem and the rules that
    # the stage without those entries selects
    assert found.problems == (
        Problem("malformed", "Docs", ()),
        Problem("unknown", "demo.ZZZ", ()),
    )
    assert _selected(found) == _selected(baseline)


@_STUB
def test_the_result_does_not_depend_on_the_order_of_the_inputs() -> None:
    """AC-8: the tables, the entries and the roots argument in two orders."""
    # Given the repository of AC-5 declared in two orders
    config, rulesets = _two_roots()
    reordered = replace(
        config, roots=freeze(dict(reversed(list(config.roots.items()))))
    )

    # When the layers apply for each order of the roots
    first = apply_layers(("web", "api"), None, config, rulesets)
    second = apply_layers(
        ("api", "web"), None, reordered, freeze(dict(reversed(list(rulesets.items()))))
    )

    # Then the results are equal, in the same order, with the effects of the root
    # layer in the order of the root names
    assert first == second
    assert list(first.rules.items()) == list(second.rules.items())
    assert [e.root for e in _layers(first, "ARC001").effects[:2]] == ["api", "web"]


@_STUB
def test_an_exclude_of_a_nested_rule_preset_stays_inside_its_entry() -> None:
    """AC-9: it records an effect and unselects nothing that another layer added."""
    # Given a preset `extra` of `demo` that includes `PAY` and excludes `ARC001`,
    # and a stage `u` that includes it, with no always field
    rulesets = _demo(recommended=(["ARC"], []), extra=(["PAY"], ["ARC001"]))
    config = _config(stages={"u": (["demo.extra"], [])}, include=[], exclude=[])

    # When the layers apply for `api` and `u`
    found = apply_layers(("api",), "u", config, rulesets)

    # Then `ARC001` stays selected with the root's add and the stage's removal by
    # its route, and `PAY001` and `PAY002` are selected by the stage
    assert _selected(found) == list(_ALL)
    assert _effects(found, "ARC001") == [
        ("root", "adds", "api"),
        ("stage", "removes", None),
    ]
    assert _layers(found, "ARC001").effects[1].routes == (
        ("demo.extra", "demo.ARC001"),
    )
    assert _effects(found, "PAY001") == [("stage", "adds", None)]
    assert _effects(found, "PAY002") == [("stage", "adds", None)]
