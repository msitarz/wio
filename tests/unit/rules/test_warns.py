# SPDX-License-Identifier: Apache-2.0
"""Tests of the warnings that the rule files and the config show together."""

from dataclasses import replace
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from tests.unit.rules.support import make_ruleset
from wio.models import config as settings
from wio.models.diagnostics import Diagnostic, sort_diagnostics
from wio.models.frozen import freeze
from wio.rules import check_warnings
from wio.rules.discovery import Discovery
lazy from wio.models.rule import Rule

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


_NAMES = ("demo", "py", "process", "broken")
type _Stages = Mapping[str, tuple[Sequence[str], Sequence[str], Sequence[str] | None]]


def _repo(*, reverse: bool = False) -> Discovery:
    """Build the rulesets of the examples: `demo`, `py` and `process`.

    Args:
        reverse: Whether to list them in the opposite order.

    Returns:
        A discovery with no diagnostic.
    """
    both = [
        make_ruleset("demo", ["ARC", "PAY"], ["ARC001", "ARC002", "ARC003", "PAY001"]),
        make_ruleset("py", ["FIX"], ["FIX001", "FIX002"], {"review": (["FIX"], [])}),
        make_ruleset("process", ["FIX"], ["FIX001"]),
    ]
    return Discovery(tuple(reversed(both) if reverse else both), ())


def _config(
    roots: Mapping[str, Sequence[str]] | None = None,
    stages: _Stages | None = None,
    **fields: Sequence[str],
) -> settings.Config:
    """Build a config in which `process` is root-independent.

    Args:
        roots: The root names with their rule presets; `api` reaching `demo` and
            `web` reaching nothing by default.
        stages: The stage names with their includes, excludes and `roots`.
        **fields: `include` and `exclude` for the always fields, and `mixed` for
            the includes of the config's rule preset of that name.

    Returns:
        The config.
    """
    given = roots if roots is not None else {"api": ["demo.ARC"], "web": []}
    built = {n: settings.Root(("src",), tuple(p)) for n, p in given.items()}
    staged = {
        n: settings.Stage(
            "g", None, None if r is None else tuple(r), tuple(i), tuple(e)
        )
        for n, (i, e, r) in (stages or {}).items()
    }
    presets = (
        {"mixed": settings.RulePreset(tuple(fields["mixed"]))}
        if "mixed" in fields
        else {}
    )
    return settings.Config(
        rulesets=freeze(
            {n: settings.Ruleset(root_independent=n == "process") for n in _NAMES}
        ),
        rule_presets=freeze(presets),
        rules_always_exclude=tuple(fields.get("exclude", ())),
        rules_always_include=tuple(fields.get("include", ())),
        stages=freeze(staged),
        roots=freeze(built),
    )


def _places(config: settings.Config, discovery: Discovery) -> list[str]:
    """List the place of each warning.

    Args:
        config: The settings.
        discovery: What the discovery returned.

    Returns:
        The places, in the order returned.
    """
    return [d.where for d in check_warnings(config, discovery)]


def test_the_warnings_of_the_discovery_are_shown_and_its_errors_are_not() -> None:
    """AC-1: each warning comes back unchanged, and the error does not."""
    # Given a discovery with two warnings and an error
    warnings = (
        Diagnostic("warning", ".agents/wio/rules/demo/ARC001-x.md", "unknown key"),
        Diagnostic("warning", ".agents/wio/rules/demo/ruleset.toml", "unknown key"),
    )
    error = Diagnostic("error", ".agents/wio/rules/bad/ruleset.toml", "does not parse")
    discovery = Discovery((), (*warnings, error))

    # When the warnings are found
    found = check_warnings(settings.Config(), discovery)

    # Then the warnings are returned as they are, and not the error
    assert found == sort_diagnostics(warnings)


_STAGES: _Stages = {
    "s": (["py.review"], [], None),
    "t": (["py.review"], [], ["api"]),
    "u": (["demo.ARC"], [], []),
    "w": (["demo.ARC"], [], ["web"]),
    "x": (["process.all"], [], None),
}


def test_a_selection_that_no_root_reaches_is_a_warning_with_a_fix() -> None:
    """AC-2: a stage's entry that no selected root reaches names the fix."""
    # Given stages that include a ruleset that no root reaches, and a ruleset that
    # the roots they select do not reach, and one that is root-independent
    config = _config(stages=_STAGES)

    # When the warnings are found
    found = check_warnings(config, _repo())

    # Then four entries are warned about and each message gives the fix
    assert [d.where for d in found] == [
        "stages.s.rules_include[0]",
        "stages.t.rules_include[0]",
        "stages.u.rules_include[0]",
        "stages.w.rules_include[0]",
    ]
    assert all(d.severity == "warning" for d in found)
    for warning, name in zip(found, ("py", "py", "demo", "demo"), strict=True):
        assert f"`{name}`" in warning.message
        assert "not root-independent" in warning.message
        assert "none of the roots" in warning.message
        assert "root_independent" in warning.message
        assert "rule_presets" in warning.message


def test_the_work_roots_and_the_always_field_count_every_root() -> None:
    """AC-3: `@work`, no `roots` and the always include count any root."""
    # Given a stage on `contract` and `@work`, and an always include, that name a
    # ruleset that no root reaches and one that `api` reaches
    config = _config(
        {"api": ["demo.ARC"], "contract": []},
        {"v": (["demo.ARC", "py.review"], [], ["contract", "@work"])},
        include=["py.FIX", "demo.ARC"],
    )

    # When the warnings are found
    places = _places(config, _repo())

    # Then only the entries of `py` are warned about
    assert places == ["rules_always_include[0]", "stages.v.rules_include[1]"]
    for warning in check_warnings(config, _repo()):
        assert "none of the roots" in warning.message
        assert "root_independent" in warning.message
        assert "rule_presets" in warning.message


def test_an_entry_that_names_several_rulesets_is_judged_for_each() -> None:
    """AC-4: a rule preset of two rulesets warns for the one no root reaches."""
    # Given a rule preset that names `demo` and, twice, the `py` that holds two
    # rules, and a stage that includes it
    config = _config(
        stages={"s": (["mixed"], [], None)},
        mixed=["demo.ARC", "py.FIX", "py.review"],
    )

    # When the warnings are found
    found = check_warnings(config, _repo())

    # Then there is one warning at the entry, and it names `py`
    assert [d.where for d in found] == ["stages.s.rules_include[0]"]
    assert "`py`" in found[0].message
    assert "`demo`" not in found[0].message


def test_excludes_and_the_entries_of_the_roots_are_not_judged() -> None:
    """AC-5: an exclude and a root's entry get no warning."""
    # Given the stages of AC-2, an exclude of `py.review` and a root that names
    # `process.all`
    stages: _Stages = {**_STAGES, "y": ([], ["py.review"], None)}
    config = _config({"api": ["demo.ARC", "process.all"], "web": []}, stages)

    # When the warnings are found
    places = _places(config, _repo())

    # Then no place is the exclude or the root's entry
    assert not [p for p in places if "rules_exclude" in p or p.startswith("roots.")]
    assert len(places) == 4


def test_a_rule_that_both_always_fields_name_is_a_warning_with_a_fix() -> None:
    """AC-6: the include entry names the exclude entries and the rules."""
    # Given an always include and an always exclude that overlap, in a ruleset
    # whose rules have names
    config = _config(
        include=["demo.ARC", "demo.PAY001"], exclude=["demo.ARC001", "demo.ARC002"]
    )
    discovery = _repo()
    renamed = [
        replace(r, name=n)
        for r, n in zip(
            discovery.rulesets[0].rules,
            ("first-rule", "second-rule", "third-rule", "pay"),
            strict=True,
        )
    ]
    named = replace(discovery.rulesets[0], rules=tuple(renamed))
    discovery = Discovery((named, *discovery.rulesets[1:]), ())

    # When the warnings are found
    found = check_warnings(config, discovery)

    # Then one warning at the first include entry names the exclude entries and
    # the rules, says the veto wins and that one of the entries should go
    assert [d.where for d in found] == ["rules_always_include[0]"]
    message = found[0].message
    assert message.index("demo.ARC001 first-rule") < message.index(
        "demo.ARC002 second-rule"
    )
    assert "`demo.ARC001`, `demo.ARC002`" in message
    assert "veto wins" in message
    assert "third-rule" not in message
    assert "ARC003" not in message
    assert "remove one of the two entries" in message


def _with_bodies(discovery: Discovery) -> Discovery:
    """Give the rules of `demo` the bodies of AC-7.

    Args:
        discovery: The discovery of the examples.

    Returns:
        A discovery whose `ARC001` has headings, `ARC002` a heading in code and
        `ARC003` a heading on a later line of its body.
    """
    bodies = {
        "ARC001": ("keep-it-small", "## Notes\n\nText.\n\n### More\n", 6),
        "ARC002": ("fenced", "```\n# not a heading\n```\n", 6),
        "ARC003": ("later-heading", "Intro.\n\n# Real\n", 7),
    }

    def given(rule: Rule) -> Rule:
        if rule.code not in bodies:
            return rule
        name, body, line = bodies[rule.code]
        path = PurePosixPath(f".agents/wio/rules/demo/{rule.code}-{name}.md")
        return replace(rule, name=name, body=body, body_line=line, path=path)

    return Discovery(
        tuple(
            replace(r, rules=tuple(map(given, r.rules))) if r.name == "demo" else r
            for r in discovery.rulesets
        ),
        (),
    )


def test_a_heading_in_a_rule_body_is_a_warning() -> None:
    """AC-7: the first real heading is the warning, and a fenced one is not."""
    # Given rules whose bodies have headings, one of them on a later line, and a
    # heading in a fenced block
    discovery = _with_bodies(_repo())

    # When the warnings are found
    found = check_warnings(settings.Config(), discovery)

    # Then two rules are warned about, each at its first heading
    places = [d.where for d in found]
    assert places == [
        ".agents/wio/rules/demo/ARC001-keep-it-small.md:6",
        ".agents/wio/rules/demo/ARC003-later-heading.md:9",
    ]
    assert "demo.ARC001 keep-it-small" in found[0].message
    assert "## Notes" in found[0].message
    assert "### More" not in found[0].message


def _in_two_orders() -> tuple[tuple[settings.Config, Discovery], ...]:
    """Build stages, an always veto, headings and warnings in two orders.

    Returns:
        The config and the discovery in one order, and in the opposite order.
    """
    roots: dict[str, list[str]] = {"web": [], "api": ["demo.ARC"]}
    stages: _Stages = {**_STAGES, "z": (["demo.PAY", "py.review"], [], None)}
    always = {"include": ["py.FIX", "demo.ARC"], "exclude": ["demo.ARC001"]}
    notes = (
        Diagnostic("warning", ".agents/wio/rules/demo/b.md", "unknown key"),
        Diagnostic("warning", ".agents/wio/rules/demo/a.md", "unknown key"),
    )
    swapped = (
        dict(reversed(list(roots.items()))),
        dict(reversed(list(stages.items()))),
    )
    return (
        (
            _config(roots, stages, **always),
            replace(_with_bodies(_repo()), diagnostics=notes),
        ),
        (
            _config(*swapped, **always),
            replace(_with_bodies(_repo(reverse=True)), diagnostics=notes[::-1]),
        ),
    )


def test_the_warnings_do_not_depend_on_the_order_of_the_inputs() -> None:
    """AC-8: two orders give equal results, and no warning is repeated."""
    # Given stages with several entries, an always veto, headings and warnings of
    # the discovery, in two orders
    first, second = _in_two_orders()

    # When the warnings are found for each
    one, two = check_warnings(*first), check_warnings(*second)

    # Then the results are equal, none repeats, and the entry of a later stage and
    # the veto are among them
    assert one == two
    assert len(set(one)) == len(one)
    assert any(d.where == "stages.z.rules_include[1]" for d in one)
    assert any("veto" in d.message for d in one)


def test_a_ruleset_that_was_left_out_gives_no_warning() -> None:
    """AC-9: an entry that names a ruleset the discovery left out is not judged."""
    # Given a stage that includes a rule of a ruleset that was left out
    config = _config(stages={"s": (["broken.ARC001"], [], None)})
    discovery = Discovery(
        _repo().rulesets,
        (Diagnostic("error", ".agents/wio/rules/broken/ruleset.toml", "bad"),),
    )

    # When the warnings are found
    found = check_warnings(config, discovery)

    # Then there is none
    assert found == ()
