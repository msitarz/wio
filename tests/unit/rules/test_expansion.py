# SPDX-License-Identifier: Apache-2.0
"""Tests of the expansion of rule presets, families and codes into rules."""

from pathlib import PurePosixPath
from typing import TYPE_CHECKING

import pytest

from wio.models.config import RulePreset
from wio.models.frozen import freeze
from wio.models.rule import LoadedRuleset, Manifest, Rule
from wio.rules.expansion import (
    ConfigScope,
    Expansion,
    Problem,
    RuleCatalog,
    RulesetScope,
    expand,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.models.rules import Routes

_STUB = pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="stub")
_CONFIG = ConfigScope()


def _rule(ruleset: str, code: str) -> Rule:
    """Build a rule of a ruleset.

    Args:
        ruleset: The ruleset's name.
        code: The rule's code, which is also the stem of its name.

    Returns:
        The rule.
    """
    name = code.lower()
    return Rule(
        ruleset=ruleset,
        code=code,
        name=name,
        description=None,
        summary="Summary.",
        body="Summary.",
        body_line=5,
        path=PurePosixPath(f".agents/wio/rules/{ruleset}/{code}-{name}.md"),
    )


def _ruleset(
    name: str,
    families: Sequence[str],
    codes: Sequence[str],
    presets: Mapping[str, tuple[Sequence[str], Sequence[str]]] | None = None,
) -> LoadedRuleset:
    """Build a ruleset with rules in the order of its codes.

    Args:
        name: The ruleset's name.
        families: The families its manifest declares.
        codes: The codes of its rules.
        presets: Its rule presets by name, with their includes and excludes.

    Returns:
        The ruleset, whose rules are in the order of family, number and code.
    """
    rules = sorted(
        (_rule(name, code) for code in codes),
        key=lambda r: (r.family, r.number, r.code),
    )
    manifest = Manifest(
        families=freeze(dict.fromkeys(families, "Topic")),
        rule_presets=freeze(
            {n: RulePreset(tuple(i), tuple(e)) for n, (i, e) in (presets or {}).items()}
        ),
    )
    return LoadedRuleset(
        name, PurePosixPath(f".agents/wio/rules/{name}"), manifest, tuple(rules)
    )


def _demo() -> LoadedRuleset:
    """Build the ruleset `demo` of AC-1.

    Returns:
        The ruleset with `ARC001`, `ARC002` and `PAY001` and a preset
        `recommended` that includes `ARC` and excludes `ARC002`.
    """
    return _ruleset(
        "demo",
        ["ARC", "PAY"],
        ["ARC001", "ARC002", "PAY001"],
        {"recommended": (["ARC"], ["ARC002"])},
    )


def _catalog(
    *rulesets: LoadedRuleset,
    aliases: Mapping[str, str] | None = None,
    presets: Mapping[str, RulePreset] | None = None,
) -> RuleCatalog:
    """Build a catalog.

    Args:
        *rulesets: The rulesets.
        aliases: Each alias with its ruleset's name.
        presets: The config's rule presets.

    Returns:
        The catalog.
    """
    return RuleCatalog(
        rulesets=freeze({r.name: r for r in rulesets}),
        aliases=freeze(dict(aliases or {})),
        presets=freeze(dict(presets or {})),
    )


def _by_code(mapping: Mapping[Rule, Routes]) -> dict[str, Routes]:
    """Key a mapping of rules by their codes, in the order of the mapping.

    Args:
        mapping: Rules with their routes.

    Returns:
        The routes by code.
    """
    return {rule.code: routes for rule, routes in mapping.items()}


@_STUB
def test_a_family_a_code_and_a_rule_preset_expand_to_rules() -> None:
    """AC-1: a rule preset takes its includes and then removes its excludes."""
    # Given `demo` with a rule preset `recommended` that includes `ARC` and
    # excludes `ARC002`
    catalog = _catalog(_demo())

    # When the preset, a code and a family are expanded in the config scope
    preset = expand(["demo.recommended"], [], _CONFIG, catalog)
    code = expand(["demo.PAY001"], [], _CONFIG, catalog)
    family = expand(["demo.PAY"], [], _CONFIG, catalog)

    # Then the preset selects `ARC001` and removes `ARC002`, and the code and the
    # family select `PAY001`, each by its route
    assert _by_code(preset.rules) == {"ARC001": (("demo.recommended", "demo.ARC"),)}
    assert _by_code(preset.removed) == {
        "ARC002": (("demo.recommended", "demo.ARC002"),)
    }
    assert _by_code(code.rules) == {"PAY001": (("demo.PAY001",),)}
    assert _by_code(family.rules) == {"PAY001": (("demo.PAY",),)}
    assert preset.problems == ()


@_STUB
def test_an_outer_include_brings_back_what_an_inner_exclude_removed() -> None:
    """AC-2: an exclude reaches only the includes of its own level."""
    # Given a config preset `backend` that includes `demo.recommended` and
    # `demo.ARC002` and excludes `demo.ARC001`
    backend = RulePreset(("demo.recommended", "demo.ARC002"), ("demo.ARC001",))
    catalog = _catalog(_demo(), presets={"backend": backend})

    # When it is expanded
    found = expand(["backend"], [], _CONFIG, catalog)

    # Then `ARC002` is selected by the outer include and `ARC001` is not, and
    # both removals are recorded with their routes
    assert _by_code(found.rules) == {"ARC002": (("backend", "demo.ARC002"),)}
    assert _by_code(found.removed) == {
        "ARC001": (("backend", "demo.ARC001"),),
        "ARC002": (("backend", "demo.recommended", "demo.ARC002"),),
    }


@_STUB
def test_an_exclude_list_removes_from_the_includes_of_its_own_list() -> None:
    """AC-2: includes `demo.ARC` and excludes `demo.ARC001`."""
    # Given the ruleset `demo`
    catalog = _catalog(_demo())

    # When the family is included and one of its codes is excluded
    found = expand(["demo.ARC"], ["demo.ARC001"], _CONFIG, catalog)

    # Then `ARC002` is selected and `ARC001` is removed
    assert list(_by_code(found.rules)) == ["ARC002"]
    assert _by_code(found.removed) == {"ARC001": (("demo.ARC001",),)}


@_STUB
def test_in_the_config_a_bare_name_is_a_rule_preset_of_the_config() -> None:
    """AC-3: a ruleset's preset or a bare code in the config is a problem."""
    # Given `demo` with a preset `recommended` and a config preset `backend`
    demo = _ruleset("demo", ["ARC"], ["ARC001"], {"recommended": (["ARC"], [])})
    backend = RulePreset(("demo.recommended",), ())
    catalog = _catalog(demo, presets={"backend": backend})

    # When `backend`, `recommended` and `ARC001` are expanded in the config scope
    config = expand(["backend"], [], _CONFIG, catalog)
    preset = expand(["recommended"], [], _CONFIG, catalog)
    code = expand(["ARC001"], [], _CONFIG, catalog)

    # Then `backend` selects `ARC001`, and the other two are one problem each
    # that selects nothing
    assert _by_code(config.rules) == {
        "ARC001": (("backend", "demo.recommended", "demo.ARC"),)
    }
    assert preset.problems == (Problem("unknown", "recommended", ()),)
    assert code.problems == (Problem("malformed", "ARC001", ()),)
    assert not preset.rules
    assert not code.rules


@_STUB
def test_in_a_manifest_a_bare_name_is_a_family_a_code_or_a_rule_preset() -> None:
    """AC-3: the entries of a manifest name its own items."""
    # Given `demo` whose preset `mixed` includes a code and its preset `local`
    demo = _ruleset(
        "demo",
        ["ARC", "PAY"],
        ["ARC001", "PAY001"],
        {"local": (["PAY"], []), "mixed": (["ARC001", "local"], [])},
    )

    # When `demo.mixed` is expanded
    found = expand(["demo.mixed"], [], _CONFIG, _catalog(demo))

    # Then it selects `ARC001` and `PAY001` by their routes
    assert _by_code(found.rules) == {
        "ARC001": (("demo.mixed", "demo.ARC001"),),
        "PAY001": (("demo.mixed", "demo.local", "demo.PAY"),),
    }


@_STUB
def test_an_alias_names_its_ruleset_and_a_route_never_shows_it() -> None:
    """AC-4: `d.recommended` and `demo.recommended` give the same expansion."""
    # Given `demo` with the alias `d`
    catalog = _catalog(_demo(), aliases={"d": "demo"})

    # When the preset is expanded by each name
    by_alias = expand(["d.recommended"], [], _CONFIG, catalog)
    by_name = expand(["demo.recommended"], [], _CONFIG, catalog)

    # Then the rules and the removals are the same, and no route names `d`
    assert by_alias.rules == by_name.rules
    assert by_alias.removed == by_name.removed
    selected = [r for rs in by_alias.rules.values() for r in rs]
    removed = [r for rs in by_alias.removed.values() for r in rs]
    assert all(part.split(".")[0] != "d" for rt in [*selected, *removed] for part in rt)


@_STUB
def test_every_ruleset_has_a_rule_preset_all_whatever_its_manifest_says() -> None:
    """AC-5: `all` holds every rule, also where a manifest defines `all`."""
    # Given `demo` and `other`, whose manifest defines `all` as `ARC001` only
    other = _ruleset("other", ["ARC"], ["ARC001", "ARC002"], {"all": (["ARC001"], [])})
    catalog = _catalog(_demo(), other)

    # When `demo.all`, `all` in the scope of `demo` and `other.all` are expanded
    config = expand(["demo.all"], [], _CONFIG, catalog)
    own = expand(["all"], [], RulesetScope("demo"), catalog)
    shadowed = expand(["other.all"], [], _CONFIG, catalog)

    # Then the first two select the three rules of `demo`, and the third selects
    # both rules of `other`
    assert list(_by_code(config.rules)) == ["ARC001", "ARC002", "PAY001"]
    assert list(_by_code(own.rules)) == ["ARC001", "ARC002", "PAY001"]
    assert list(_by_code(shadowed.rules)) == ["ARC001", "ARC002"]


@_STUB
def test_a_rule_reached_twice_has_both_routes_sorted() -> None:
    """AC-6: one rule, two routes."""
    # Given a config preset that includes `demo.recommended` and `demo.ARC001`
    backend = RulePreset(("demo.recommended", "demo.ARC001"), ())
    catalog = _catalog(_demo(), presets={"backend": backend})

    # When it is expanded
    found = expand(["backend"], [], _CONFIG, catalog)

    # Then `ARC001` is one rule with both routes in order
    assert _by_code(found.rules) == {
        "ARC001": (
            ("backend", "demo.ARC001"),
            ("backend", "demo.recommended", "demo.ARC"),
        )
    }


@_STUB
def test_a_cycle_is_one_problem_and_the_rest_still_expands() -> None:
    """AC-7: two presets that include each other."""
    # Given presets `a` and `b` of `demo` that include each other
    demo = _ruleset(
        "demo",
        ["ARC"],
        ["ARC001", "ARC002"],
        {"a": (["ARC001", "b"], []), "b": (["ARC002", "a"], [])},
    )

    # When `demo.a` is expanded
    found = expand(["demo.a"], [], _CONFIG, _catalog(demo))

    # Then one `cycle` problem has the route that closes it, and both rules are
    # selected
    assert found.problems == (Problem("cycle", "a", ("demo.a", "demo.b", "demo.a")),)
    assert list(_by_code(found.rules)) == ["ARC001", "ARC002"]


@_STUB
def test_what_cannot_be_expanded_is_a_problem_that_selects_nothing() -> None:
    """AC-8: unknown, malformed and qualified entries."""
    # Given a preset `broken` whose entries include every kind of problem
    entries = ["ARC001", "ZZZ", "ARC999", "none", "Docs", "demo.ARC"]
    demo = _ruleset("demo", ["ARC"], ["ARC001"], {"broken": (entries, [])})
    catalog = _catalog(demo)

    # When `demo.broken` and `nope.ARC` are expanded
    broken = expand(["demo.broken"], [], _CONFIG, catalog)
    nope = expand(["nope.ARC"], [], _CONFIG, catalog)

    # Then `ARC001` is selected, each problem names its entry and the preset it
    # was found in, and an unknown ruleset is one problem
    route = ("demo.broken",)
    assert list(_by_code(broken.rules)) == ["ARC001"]
    assert broken.problems == (
        Problem("unknown", "ARC999", route),
        Problem("malformed", "Docs", route),
        Problem("unknown", "ZZZ", route),
        Problem("qualified-in-manifest", "demo.ARC", route),
        Problem("unknown", "none", route),
    )
    assert nope.problems == (Problem("unknown", "nope.ARC", ()),)


@_STUB
def test_a_declared_family_that_holds_no_rule_is_no_problem() -> None:
    """AC-9: it selects nothing."""
    # Given `demo` that declares `ARC` and `PAY` and holds only `ARC001`
    demo = _ruleset("demo", ["ARC", "PAY"], ["ARC001"])

    # When `demo.PAY` is expanded
    found = expand(["demo.PAY"], [], _CONFIG, _catalog(demo))

    # Then it selects nothing and reports nothing
    assert not found.rules
    assert found.problems == ()


def _two_orders() -> tuple[Expansion, Expansion]:
    """Expand a preset over the catalog of AC-6, enlarged and declared in two orders.

    The catalog adds a ruleset `other`, an exclude of the preset and entries that
    name nothing, so that there are removals and problems whose order can be
    compared; the rulesets, the config's preset table and the entries of the
    preset are each in another order in the second catalog.

    Returns:
        The expansion of each order.
    """
    entries = ["demo.recommended", "other.ARC", "demo.ARC001", "none", "nope.X"]
    excludes = ["other.ARC002"]
    results = []
    for reverse in (False, True):
        step = -1 if reverse else 1
        demo = _ruleset(
            "demo",
            ["ARC", "PAY"],
            ["ARC001", "ARC002", "PAY001"],
            {"recommended": (["ARC", "ZZZ"], ["ARC002"])},
        )
        other = _ruleset("other", ["ARC"], ["ARC002", "ARC001"])
        backend = RulePreset(tuple(entries[::step]), tuple(excludes[::step]))
        presets = {"zeta": RulePreset((), ()), "backend": backend}
        order = dict(reversed(presets.items())) if reverse else presets
        catalog = _catalog(*[demo, other][::step], presets=order)
        results.append(expand(["backend"], [], _CONFIG, catalog))
    return results[0], results[1]


@_STUB
def test_the_expansion_does_not_depend_on_the_order_of_the_inputs() -> None:
    """AC-10: rules, removals, routes and problems come in the same order."""
    # Given a catalog and the entries of a preset declared in two orders

    # When the preset is expanded on each
    first, second = _two_orders()

    # Then both list their rules, removals, routes and problems alike, the rules
    # by ruleset, family and number, the removals likewise, and the problems by
    # route, then reference
    assert list(first.rules.items()) == list(second.rules.items())
    assert list(first.removed.items()) == list(second.removed.items())
    assert first.problems == second.problems
    assert [(r.ruleset, r.code) for r in first.rules] == [
        ("demo", "ARC001"),
        ("other", "ARC001"),
    ]
    assert [(r.ruleset, r.code) for r in first.removed] == [
        ("demo", "ARC002"),
        ("other", "ARC002"),
    ]
    assert hash(first) == hash(second)
    assert first.problems == (
        Problem("unknown", "none", ("backend",)),
        Problem("unknown", "nope.X", ("backend",)),
        Problem("unknown", "ZZZ", ("backend", "demo.recommended")),
    )


@_STUB
def test_the_rulesets_that_the_includes_name_are_returned() -> None:
    """AC-11: by canonical name, also when the excludes leave none of their rules."""
    # Given `demo` with the alias `d`, `other` and `third`
    other = _ruleset("other", ["ARC"], ["ARC001"])
    third = _ruleset("third", ["ARC"], ["ARC001"])
    catalog = _catalog(_demo(), other, third, aliases={"d": "demo"})

    # When includes are expanded with excludes, and entries that name nothing
    found = expand(
        ["d.recommended", "other.ARC"],
        ["other.ARC001", "third.ARC001"],
        _CONFIG,
        catalog,
    )
    wrapped = RulePreset(("third.ARC",), ("third.ARC001",))
    nested = expand(["wrap"], [], _CONFIG, _catalog(third, presets={"wrap": wrapped}))
    unknown_ruleset = expand(["nope.ARC"], [], _CONFIG, catalog)
    unknown_family = expand(["other.XYZ"], [], _CONFIG, catalog)

    # Then `demo` and `other` are named, no rule of `other` is left, `third` is
    # not named, and an entry that names nothing names no ruleset
    assert found.rulesets == frozenset({"demo", "other"})
    assert all(rule.ruleset != "other" for rule in found.rules)
    assert nested.rulesets == frozenset({"third"})
    assert not nested.rules
    assert unknown_ruleset.rulesets == frozenset()
    assert unknown_family.rulesets == frozenset()
