# SPDX-License-Identifier: Apache-2.0
"""Tests of the rules that some include entry of the config delivers."""

from typing import TYPE_CHECKING

from tests.unit.rules.support import make_ruleset
from wio.models.config import Config, Root, Ruleset, Stage
from wio.models.frozen import freeze
from wio.rules import Origin, SelectedAnywhere, selected_anywhere
lazy from wio.models.rule import LoadedRuleset

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.models.rule import Rule

type _Presets = Mapping[str, tuple[Sequence[str], Sequence[str]]]


def _repo(
    presets: _Presets | None = None, *, reverse: bool = False
) -> Mapping[str, LoadedRuleset]:
    """Build the rulesets `demo` and `process` of the contract.

    Args:
        presets: The rule presets of `demo`; `recommended` by default.
        reverse: Whether to build them in the opposite order.

    Returns:
        The rulesets by name.
    """
    given = presets or {"recommended": (["ARC"], ["ARC002"])}
    codes = ["ARC001", "ARC002", "PAY001", "PAY002"]
    both = {
        "demo": make_ruleset("demo", ["ARC", "PAY"], codes, given),
        "process": make_ruleset("process", ["FIX"], ["FIX001"]),
    }
    return freeze(dict(reversed(both.items())) if reverse else both)


def _config(
    roots: Mapping[str, Sequence[str]] | None = None,
    stages: Mapping[str, Sequence[str]] | None = None,
    **fields: Sequence[str],
) -> Config:
    """Build the config of AC-1, with the parts that a test replaces.

    Args:
        roots: The root names with their rule presets; `api` by default.
        stages: The stage names with their includes; `s` by default.
        **fields: `include`, `exclude`, `stage_exclude` for the always fields
            and the excludes of every stage.

    Returns:
        The config.
    """
    given_roots = roots or {"api": ["demo.recommended"]}
    given_stages = stages or {"s": ["demo.PAY001"]}
    skip = tuple(fields.get("stage_exclude", ()))
    built = {n: Root(("src",), tuple(p)) for n, p in given_roots.items()}
    staged = {
        n: Stage("g", None, None, tuple(i), skip) for n, i in given_stages.items()
    }
    return Config(
        roots=freeze(built),
        stages=freeze(staged),
        rules_always_include=tuple(fields.get("include", ["process.all"])),
        rules_always_exclude=tuple(fields.get("exclude", ())),
    )


def _keys(found: SelectedAnywhere) -> list[str]:
    """List the qualified codes of the selected rules in order.

    Args:
        found: The result.

    Returns:
        The codes.
    """
    return [f"{r.ruleset}.{r.code}" for r in found.selected]


def _origins(
    entry: Mapping[Rule, tuple[Origin, ...]], code: str
) -> list[tuple[str, str | None]]:
    """List the layer and name of the origins of a rule.

    Args:
        entry: `selected` or `removed` of a result.
        code: The qualified code.

    Returns:
        The origins' layers and names, in order.
    """
    (found,) = [v for r, v in entry.items() if f"{r.ruleset}.{r.code}" == code]
    return [(o.layer, o.name) for o in found]


def test_a_rule_that_an_entry_delivers_is_selected_with_its_origins() -> None:
    """AC-1: the keys are what the entries deliver, and removed has the rest."""
    # Given a root, a stage and an always include that each deliver rules
    config = _config()

    # When the rules selected anywhere are found
    found = selected_anywhere(config, _repo())

    # Then the delivered rules are keys with their origins, and what the exclude
    # of the rule preset took out is removed, with its route
    assert _keys(found) == ["demo.ARC001", "demo.PAY001", "process.FIX001"]
    assert _origins(found.selected, "demo.ARC001") == [("root", "api")]
    assert _origins(found.selected, "demo.PAY001") == [("stage", "s")]
    assert _origins(found.selected, "process.FIX001") == [("always-include", None)]
    (removed,) = found.removed.items()
    assert removed[0].code == "ARC002"
    assert removed[1][0].routes == (("demo.recommended", "demo.ARC002"),)


def test_a_rule_with_several_origins_has_all_of_them_in_order() -> None:
    """AC-2: layers in order, then names, each origin holding all its routes."""
    # Given several roots, stages and an always include that deliver ARC001
    config = _config(
        roots={"web": ["demo.recommended", "demo.ARC001"], "api": ["demo.ARC"]},
        stages={"t": ["demo.ARC001"], "s": ["demo.ARC001"]},
        include=["demo.ARC001"],
    )

    # When the rules selected anywhere are found
    found = selected_anywhere(config, _repo())

    # Then its origins are sorted by layer and by name
    assert _origins(found.selected, "demo.ARC001") == [
        ("root", "api"),
        ("root", "web"),
        ("stage", "s"),
        ("stage", "t"),
        ("always-include", None),
    ]


def test_an_exclude_of_a_stage_or_the_veto_does_not_unselect() -> None:
    """AC-3: a view's excludes leave the rule selected."""
    # Given a stage exclude and an always exclude of delivered rules
    config = _config(stage_exclude=["demo.PAY001"], exclude=["demo.ARC001"])

    # When the rules selected anywhere are found
    found = selected_anywhere(config, _repo())

    # Then both rules are still keys
    assert {"demo.ARC001", "demo.PAY001"} <= set(_keys(found))


def test_an_entry_that_no_root_reaches_still_delivers() -> None:
    """AC-4: an entry counts whatever the roots."""
    # Given a ruleset that no root reaches and a stage that includes its preset
    repo = freeze({**_repo(), "py": make_ruleset("py", ["PYT"], ["PYT001"])})
    config = _config(stages={"s": ["py.all"]})

    # When the rules selected anywhere are found
    found = selected_anywhere(config, repo)

    # Then its rule has the origin of that stage
    assert _origins(found.selected, "py.PYT001") == [("stage", "s")]


def test_what_cannot_be_expanded_delivers_nothing_and_raises_nothing() -> None:
    """AC-5: the bad entries add no key and the rest are found."""
    # Given a stage with a missing code, a malformed entry and a rule preset
    # that includes itself
    repo = _repo({"loop": (["ARC001", "loop"], [])})
    config = _config(
        stages={"s": ["demo.ZZZ", "Docs", "demo.loop", "demo.PAY001"]},
        include=[],
        roots={"api": []},
    )

    # When the rules selected anywhere are found
    found = selected_anywhere(config, repo)

    # Then the good entries are found with the cycle's route, and no other key
    assert _keys(found) == ["demo.ARC001", "demo.PAY001"]
    (arc, _pay) = found.selected.values()
    assert arc[0].routes == (("demo.loop", "demo.ARC001"),)


def test_an_alias_gives_the_canonical_name() -> None:
    """AC-6: the routes name the ruleset and not its alias."""
    # Given a stage that includes a rule by the alias of its ruleset
    config = _config(stages={"s": ["d.PAY001"]}, include=[], roots={"api": []})
    config = Config(
        roots=config.roots,
        stages=config.stages,
        rulesets=freeze({"demo": Ruleset(alias="d")}),
    )

    # When the rules selected anywhere are found
    found = selected_anywhere(config, _repo())

    # Then the key and the routes carry the canonical name
    assert _keys(found) == ["demo.PAY001"]
    assert found.selected[next(iter(found.selected))][0].routes == (("demo.PAY001",),)


def test_the_answer_is_deterministic_and_needs_no_file() -> None:
    """AC-7: two orders give equal results, and an empty config gives nothing."""
    # Given the same repository declared in two orders, and an empty config
    first = (_config(roots={"b": ["demo.ARC"], "a": ["demo.PAY"]}), _repo())
    second = (
        _config(roots={"a": ["demo.PAY"], "b": ["demo.ARC"]}),
        _repo(reverse=True),
    )

    # When the rules selected anywhere are found for each
    one, two = selected_anywhere(*first), selected_anywhere(*second)
    nothing = selected_anywhere(Config(), freeze({}))

    # Then the first two are equal, in both mappings, and the last is empty
    assert (one.selected, one.removed) == (two.selected, two.removed)
    assert list(one.selected) == list(two.selected)
    assert not nothing.selected
    assert not nothing.removed


def test_what_the_excludes_of_rule_presets_took_out_is_recorded() -> None:
    """AC-8: removed has the rule and the entry, also when it is selected."""
    # Given a second root and a stage whose rule presets exclude rules
    presets: _Presets = {
        "recommended": (["ARC"], ["ARC002"]),
        "family": (["ARC"], []),
        "extra": (["PAY"], ["PAY002"]),
    }
    config = _config(
        roots={"api": ["demo.recommended"], "web": ["demo.family"]},
        stages={"u": ["demo.extra"]},
    )

    # When the rules selected anywhere are found
    found = selected_anywhere(config, _repo(presets))

    # Then ARC002 is selected through `web` and removed through `api`, and PAY002
    # is removed through the stage
    assert _origins(found.selected, "demo.ARC002") == [("root", "web")]
    assert _origins(found.removed, "demo.ARC002") == [("root", "api")]
    assert _origins(found.removed, "demo.PAY002") == [("stage", "u")]


def test_an_origin_holds_all_the_routes_of_its_entry_sorted() -> None:
    """C-1: two rule presets of one root that reach a rule give one origin."""
    # Given a root whose two rule presets both include ARC001, listed unsorted
    presets: _Presets = {"zed": (["ARC001"], []), "alpha": (["ARC"], [])}
    config = _config(roots={"api": ["demo.zed", "demo.alpha"]}, include=[])

    # When the rules selected anywhere are found
    found = selected_anywhere(config, _repo(presets))

    # Then the rule has one origin with both routes, sorted
    (origin,) = found.selected[next(iter(found.selected))]
    assert origin.routes == (
        ("demo.alpha", "demo.ARC"),
        ("demo.zed", "demo.ARC001"),
    )
    assert hash(found) == hash(selected_anywhere(config, _repo(presets)))
