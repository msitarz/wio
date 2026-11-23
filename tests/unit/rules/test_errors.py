# SPDX-License-Identifier: Apache-2.0
"""Tests of the errors that the rule files and the config show together."""

from typing import TYPE_CHECKING

import pytest

from tests.unit.rules.support import make_ruleset
from wio.models.config import Config, Root, RulePreset, Ruleset, Stage
from wio.models.diagnostics import Diagnostic, sort_diagnostics
from wio.models.frozen import freeze
from wio.rules import check_errors
from wio.rules.discovery import Discovery

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.models.rule import LoadedRuleset

_PENDING = pytest.mark.xfail(raises=NotImplementedError, strict=True)
_MANIFEST = ".agents/wio/rules/demo/ruleset.toml"
type _Presets = Mapping[str, tuple[Sequence[str], Sequence[str]]]
type _Lists = Mapping[str, Sequence[str]]


def _demo(
    presets: _Presets | None = None, codes: Sequence[str] = ("ARC001",)
) -> Discovery:
    """Build a discovery of the ruleset `demo`, which declares `ARC` and `PAY`.

    Args:
        presets: The rule presets of its manifest, with their includes and
            excludes; `recommended` that includes `ARC` by default.
        codes: The codes of its rules.

    Returns:
        The discovery, with no diagnostic.
    """
    given = presets or {"recommended": (["ARC"], [])}
    return Discovery((make_ruleset("demo", ["ARC", "PAY"], codes, given),), ())


def _with(discovery: Discovery, *more: LoadedRuleset) -> Discovery:
    """Add rulesets to a discovery.

    Args:
        discovery: The discovery.
        *more: The rulesets to add.

    Returns:
        A discovery with all of them.
    """
    return Discovery((*discovery.rulesets, *more), discovery.diagnostics)


def _config(
    roots: _Lists | None = None,
    stages: Mapping[str, tuple[Sequence[str], Sequence[str]]] | None = None,
    **fields: Sequence[str],
) -> Config:
    """Build a config with the parts that a test sets.

    Args:
        roots: The root names with their rule presets.
        stages: The stage names with their includes and excludes.
        **fields: `include` and `exclude` for the always fields, and `backend` for
            the includes of the config's rule preset of that name.

    Returns:
        The config.
    """
    built = {n: Root(("src",), tuple(p)) for n, p in (roots or {}).items()}
    staged = {
        n: Stage("g", None, None, tuple(i), tuple(e))
        for n, (i, e) in (stages or {}).items()
    }
    named = (
        {"backend": RulePreset(tuple(fields["backend"]))} if "backend" in fields else {}
    )
    return Config(
        roots=freeze(built),
        stages=freeze(staged),
        rules_always_include=tuple(fields.get("include", ())),
        rules_always_exclude=tuple(fields.get("exclude", ())),
        rule_presets=freeze(named),
        rulesets=freeze({"process": Ruleset(root_independent=True)}),
    )


def _found(config: Config, discovery: Discovery) -> list[tuple[str, str]]:
    """List the place and the message of each error.

    Args:
        config: The settings.
        discovery: What the discovery returned.

    Returns:
        The places and messages, in the order returned.
    """
    return [(d.where, d.message) for d in check_errors(config, discovery)]


@_PENDING
def test_the_errors_of_the_discovery_are_shown_and_its_warnings_are_not() -> None:
    """AC-1: each error comes back unchanged, and the warning does not."""
    # Given a discovery with two errors and a warning
    errors = (
        Diagnostic("error", ".agents/wio/rules/demo/ARC001-x.md:1", "block not closed"),
        Diagnostic("error", f"{_MANIFEST}", "does not parse"),
    )
    warning = Diagnostic("warning", ".agents/wio/rules/demo/ARC002-y.md", "unknown key")
    discovery = Discovery((), (*errors, warning))

    # When the errors are found
    found = check_errors(Config(), discovery)

    # Then the two errors are returned as they are, and not the warning
    assert found == sort_diagnostics(errors)


_BAD = [
    "demo.ZZZ",
    "demo.ARC999",
    "demo.none",
    "demo.ARC",
    "demo.ARC001",
    "demo.recommended",
]


@_PENDING
def test_a_reference_of_the_config_that_names_nothing_is_an_error() -> None:
    """AC-2: each field that takes references reports its entries that fail."""
    # Given references that fail and references that name something, in every
    # field that takes them
    config = _config(
        {"api": ["demo.none", "demo.recommended"]},
        {"s": (_BAD, _BAD)},
        include=_BAD,
        exclude=["demo.ZZZ", "demo.ARC999"],
        backend=_BAD,
    )

    # When the errors are found
    found = _found(config, _demo())

    # Then each failing entry is one error at its key path, and no valid one is
    places = {where for where, _ in found}
    expected = {
        "roots.api.rule_presets[0]",
        *{f"rules_always_exclude[{i}]" for i in (0, 1)},
    }
    for key in (
        "stages.s.rules_include",
        "stages.s.rules_exclude",
        "rule_presets.backend.rules_include",
        "rules_always_include",
    ):
        expected |= {f"{key}[{i}]" for i in (0, 1, 2)}
    assert places == expected
    assert len(found) == len(expected)


@_PENDING
def test_the_message_lists_what_exists() -> None:
    """AC-2: an unknown family, code and rule preset each list their siblings."""
    # Given a stage that includes an unknown family, code and rule preset
    config = _config(stages={"s": (["demo.ZZZ", "demo.ARC999", "demo.none"], [])})

    # When the errors are found
    found = dict(_found(config, _demo()))

    # Then each message lists the families, the codes of its family and the rule
    # presets that exist
    assert "`ARC`" in found["stages.s.rules_include[0]"]
    assert "`ARC001`" in found["stages.s.rules_include[1]"]
    assert "`recommended`" in found["stages.s.rules_include[2]"]


_LOCAL: _Presets = {"local": (["ZZZ", "Docs", "demo.ARC"], ["ARC999"])}


@_PENDING
def test_a_reference_of_a_manifest_that_cannot_be_used_is_an_error() -> None:
    """AC-3: a name that is nothing, a malformed one and a qualified one fail."""
    # Given a manifest whose rule preset has three entries that cannot be used
    discovery = _demo(_LOCAL)

    # When the errors are found
    found = _found(Config(), discovery)

    # Then there are four errors at the keys of the manifest, with their reasons
    base = f"{_MANIFEST}#rule_presets.local"
    assert [w for w, _ in found] == [
        f"{base}.rules_exclude[0]",
        f"{base}.rules_include[0]",
        f"{base}.rules_include[1]",
        f"{base}.rules_include[2]",
    ]
    assert "ARC999" in found[0][1]
    assert "ZZZ" in found[1][1]
    assert "not a reference" in found[2][1]
    assert "qualified" in found[3][1]


@_PENDING
def test_a_fault_is_reported_once_however_many_entries_reach_it() -> None:
    """AC-4: the entries that reach a faulty rule preset get no error."""
    # Given the manifest of AC-3 reached by a config rule preset, a root, a stage
    # and an always include
    config = _config(
        {"api": ["backend"]},
        {"s": (["backend"], [])},
        include=["demo.local"],
        backend=["demo.local"],
    )

    # When the errors are found
    found = _found(config, _demo(_LOCAL))

    # Then the four errors of the manifest are returned once, and no other
    assert len(found) == 4
    assert all(where.startswith(_MANIFEST) for where, _ in found)


@_PENDING
def test_a_cycle_of_rule_presets_is_one_error_that_names_them() -> None:
    """AC-5: each cycle is one error at its first preset, and a bystander none."""
    # Given presets that include each other, one that includes itself, and one
    # that includes the first
    discovery = _demo(
        {"a": (["b"], []), "b": (["a"], []), "c": (["c"], []), "d": (["a"], [])}
    )

    # When the errors are found
    found = _found(Config(), discovery)

    # Then there is one error for each cycle, and none for `d`
    assert [w for w, _ in found] == [
        f"{_MANIFEST}#rule_presets.a.rules_include",
        f"{_MANIFEST}#rule_presets.c.rules_include",
    ]
    assert "`a`" in found[0][1]
    assert "`b`" in found[0][1]
    assert "`c`" in found[1][1]


@_PENDING
def test_a_manifest_cannot_define_all() -> None:
    """AC-6: a preset called `all` is an error, and referring to `all` is not."""
    # Given a manifest that defines `all` and a preset that includes it, and a
    # config entry `demo.all`
    discovery = _demo({"all": (["ARC"], []), "x": (["all"], [])})
    config = _config(stages={"s": (["demo.all"], [])})

    # When the errors are found
    found = _found(config, discovery)

    # Then the only error is at the preset `all` and says that it is reserved
    assert [w for w, _ in found] == [f"{_MANIFEST}#rule_presets.all"]
    assert "reserved" in found[0][1]


def _process() -> LoadedRuleset:
    """Build the root-independent ruleset `process` with the rule `FIX001`.

    Returns:
        The ruleset.
    """
    return make_ruleset("process", ["FIX"], ["FIX001"])


@_PENDING
def test_a_root_must_not_reach_a_root_independent_ruleset() -> None:
    """AC-7: the entry of the root that reaches it is the error, not the stage."""
    # Given a root whose second entry names `process`, and a stage that includes
    # one of its rules
    config = _config(
        {"api": ["demo.recommended", "process.all"]},
        {"s": (["process.FIX001"], [])},
    )

    # When the errors are found
    found = _found(config, _with(_demo(), _process()))

    # Then one error at that entry names the ruleset and the root
    assert [w for w, _ in found] == ["roots.api.rule_presets[1]"]
    assert "`process`" in found[0][1]
    assert "`api`" in found[0][1]


@_PENDING
def test_a_root_reaching_it_through_a_rule_preset_names_the_preset() -> None:
    """AC-7: the error is at the root's entry and names the config's preset."""
    # Given a config rule preset that includes `process.all`, a root that
    # includes it, and a stage that includes it
    config = _config(
        {"api": ["demo.recommended", "backend"]},
        {"s": (["backend"], [])},
        backend=["process.all"],
    )

    # When the errors are found
    found = _found(config, _with(_demo(), _process()))

    # Then one error at the root's entry names `process`, `api` and `backend`
    assert [w for w, _ in found] == ["roots.api.rule_presets[1]"]
    assert all(f"`{name}`" in found[0][1] for name in ("process", "api", "backend"))


@_PENDING
def test_a_reference_to_what_the_discovery_left_out_is_reported() -> None:
    """AC-8: a rule or a ruleset that was left out is a reference to nothing."""
    # Given a ruleset whose rules were left out, a ruleset that was left out
    # whole, and a stage that includes one rule of each
    left = Diagnostic("error", ".agents/wio/rules/demo", "two rules share ARC001")
    lost = Diagnostic(
        "error", ".agents/wio/rules/broken/ruleset.toml", "does not parse"
    )
    discovery = Discovery(_demo(codes=()).rulesets, (left, lost))
    config = _config(stages={"s": (["demo.ARC001", "broken.ARC001"], [])})

    # When the errors are found
    found = _found(config, discovery)

    # Then the errors of the discovery come with one error at each entry
    places = {where for where, _ in found}
    assert places == {
        ".agents/wio/rules/demo",
        ".agents/wio/rules/broken/ruleset.toml",
        "stages.s.rules_include[0]",
        "stages.s.rules_include[1]",
    }
    assert "not a ruleset that was read" in dict(found)["stages.s.rules_include[1]"]


@_PENDING
def test_a_family_that_holds_no_rule_is_not_an_error() -> None:
    """AC-10: a declared family without a rule is a valid reference."""
    # Given a manifest that declares `ARC` and `PAY` and holds only `ARC001`, and
    # a stage that includes `demo.PAY`
    config = _config(stages={"s": (["demo.PAY"], [])})

    # When the errors are found
    found = _found(config, _demo())

    # Then there is none
    assert found == []


@_PENDING
def test_the_errors_do_not_depend_on_the_order_of_the_inputs() -> None:
    """AC-11: two orders of the tables and the rulesets give equal results."""
    # Given a config and rulesets with errors of several kinds, in two orders
    presets: _Presets = {**_LOCAL, "a": (["b"], []), "b": (["a"], [])}
    roots = {"web": ["process.all"], "api": ["demo.none"]}
    stages = {"t": (["demo.ZZZ"], []), "s": (["demo.ARC999"], [])}
    forward = _config(roots, stages)
    backward = _config(dict(reversed(roots.items())), dict(reversed(stages.items())))
    first = _with(_demo(presets), _process())
    second = Discovery(tuple(reversed(first.rulesets)), first.diagnostics)

    # When the errors are found for each
    one, two = check_errors(forward, first), check_errors(backward, second)

    # Then the results are equal
    assert one == two
    assert one
