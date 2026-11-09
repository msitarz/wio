# SPDX-License-Identifier: Apache-2.0
"""Tests of the checks of rule references and rulesets.

A directory of the in-memory file system exists when a stored file lies below
it, so a ruleset directory is held by a file such as its `ruleset.toml`.
"""

from typing import TYPE_CHECKING

import pytest

from tests.unit.config.fakes import (
    ROOT,
    MemoryFileSystem,
    diagnostic_lines,
    make_config,
)
from wio.config import CheckInputs, selection
from wio.models.config import Root, RulePreset, Ruleset, Stage

if TYPE_CHECKING:
    from collections.abc import Callable

    from wio.models.config import Config

_RULES = ".agents/wio/rules"
_FORM = "a lowercase letter, then lowercase letters, digits, `-` and `_`"


def _fs(*present: str) -> MemoryFileSystem:
    """Build a file system that holds some files below the repository root.

    Args:
        *present: The files, relative to the repository root.

    Returns:
        The file system.
    """
    return MemoryFileSystem({ROOT / name: "" for name in present})


def _inputs(*present: str) -> CheckInputs:
    """Build the inputs of a check over a file system that holds some files.

    Args:
        *present: The files, relative to the repository root.

    Returns:
        The inputs.
    """
    return CheckInputs(ROOT, _fs(*present))


def _docs() -> CheckInputs:
    """Build inputs with a ruleset `docs` that has a manifest.

    Returns:
        The inputs.
    """
    return _inputs(f"{_RULES}/docs/ruleset.toml")


def _stage(*include: str, exclude: tuple[str, ...] = ()) -> Stage:
    """Build a stage that selects rules.

    Args:
        *include: Its `rules_include`.
        exclude: Its `rules_exclude`.

    Returns:
        The stage.
    """
    return Stage(goal="g", rules_include=include, rules_exclude=exclude)


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("mine", selection.Bare("mine")),
        ("define-bugfix", selection.Bare("define-bugfix")),
        ("docs.DOC", selection.Qualified("docs", "DOC")),
        ("docs.DOC001", selection.Qualified("docs", "DOC001")),
        ("docs.all", selection.Qualified("docs", "all")),
        ("DOC", "is not a rule preset name"),
        ("Docs.DOC", "the ruleset part `Docs`"),
        ("docs.Doc1", "the item `Doc1`"),
        ("docs.DOC001.x", "has more than one dot"),
        ("docs.", "the item ``"),
        (".DOC", "the ruleset part ``"),
    ],
)
def test_a_reference_has_the_form_of_its_kind(
    text: str, kind: selection.Reference | str
) -> None:
    """AC-1: a bare name, a ruleset name and the parts of a qualified reference."""
    # Given a reference as the config writes it

    # When its form is judged
    found = selection.parse_reference(text)

    # Then a bare name and a qualified reference with parts in their forms are
    # told apart, and any other text says which part is wrong and the form it
    # should have
    if isinstance(kind, str):
        assert isinstance(found, selection.Malformed)
        assert kind in found.message
        assert _FORM in found.message or "bare name or" in found.message
    else:
        assert found == kind


def test_the_directories_are_read_with_is_dir_before_list_dir() -> None:
    """AC-2, AC-5: the entries that are directories, and which hold a manifest."""
    # Given `.agents/wio/rules` with a ruleset `docs` that has a `ruleset.toml`, a
    # directory `bare` without one, and a stray file
    files = _fs(
        f"{_RULES}/docs/ruleset.toml", f"{_RULES}/bare/rule.md", f"{_RULES}/README.md"
    )

    # When the rulesets are read
    found = selection.read_rulesets(CheckInputs(ROOT, files))

    # Then the names are `bare` and `docs`, sorted, only `bare` is without a
    # manifest, the file is ignored, and `is_dir` of the rules directory was asked
    # before `list_dir`
    assert found == selection.Rulesets(("bare", "docs"), ("bare",))
    asked = [call for call, _ in files.calls]
    assert asked.index("is_dir") < asked.index("list_dir")


def test_wrong_forms_get_one_error_each_and_no_error_about_a_ruleset() -> None:
    """AC-1: each entry has one error, and the directory `My Rules` another."""
    # Given a stage `define` whose `rules_include` is `["Docs.DOC", "docs.Doc1",
    # "docs.DOC001.x"]`, with a ruleset `docs`, and a directory `My Rules` holding
    # a `ruleset.toml`, under `.agents/wio/rules`
    config = make_config(
        stages={"define": _stage("Docs.DOC", "docs.Doc1", "docs.DOC001.x")}
    )
    inputs = _inputs(f"{_RULES}/docs/ruleset.toml", f"{_RULES}/My Rules/ruleset.toml")

    # When the rule references and the rulesets are checked
    found = diagnostic_lines(
        [
            *selection.check_rule_references(config, inputs),
            *selection.check_rulesets(config, inputs),
        ]
    )

    # Then each entry has one error at `stages.define.rules_include[<n>]` that
    # names the form that part should have and none about an unknown ruleset, and
    # the directory has one error at `.agents/wio/rules/My Rules` that names the
    # form of a ruleset name
    assert len(found) == 4
    assert found[3] == (
        f"error: {_RULES}/My Rules: `My Rules` is not a ruleset name; a ruleset "
        f"name is {_FORM}."
    )
    assert "the ruleset part `Docs`" in found[0]
    assert "the item `Doc1`" in found[1]
    assert "more than one dot" in found[2]
    assert all("unknown ruleset" not in line for line in found)


def test_an_unknown_ruleset_and_an_unknown_preset_list_what_exists() -> None:
    """AC-2: the ruleset part must be known, and a bare name a config preset."""
    # Given a stage `define` with `rules_include = ["docz.DOC", "mine",
    # "docs.DOC"]` where there is a ruleset `docs` and no rule preset `mine`
    config = make_config(stages={"define": _stage("docz.DOC", "mine", "docs.DOC")})

    # When the rule references are checked
    found = diagnostic_lines(selection.check_rule_references(config, _docs()))

    # Then an error at `stages.define.rules_include[0]` names `docz` and lists the
    # rulesets and aliases, one at `stages.define.rules_include[1]` lists the
    # config's rule presets, and the third passes
    assert found == [
        (
            "error: stages.define.rules_include[0]: unknown ruleset `docz`. "
            "Declared rulesets and aliases: `docs`."
        ),
        (
            "error: stages.define.rules_include[1]: unknown rule preset `mine`. "
            "No rule presets are declared."
        ),
    ]


def test_a_root_and_an_always_field_resolve_their_references() -> None:
    """AC-2: a root's `rule_presets` and `rules_always_include` are judged."""
    # Given a root `wio` with `rule_presets = ["docz.all"]`, where there is no
    # ruleset or alias `docz`, and `rules_always_include = ["nope"]`
    config = make_config(
        roots={"wio": Root(paths=("src",), rule_presets=("docz.all",))},
        rule_presets={"mine": RulePreset()},
        always_include=["nope"],
    )

    # When the rule references are checked
    found = diagnostic_lines(selection.check_rule_references(config, _docs()))

    # Then an error at `roots.wio.rule_presets[0]` names `docz` and one at
    # `rules_always_include[0]` lists the config's rule presets
    assert found == [
        (
            "error: roots.wio.rule_presets[0]: unknown ruleset `docz`. "
            "Declared rulesets and aliases: `docs`."
        ),
        (
            "error: rules_always_include[0]: unknown rule preset `nope`. "
            "Declared rule presets: `mine`."
        ),
    ]


def test_no_rules_directory_is_asked_about_before_it_is_listed() -> None:
    """AC-2: a repository without `.agents/wio/rules` has no ruleset and no error."""
    # Given a repository without `.agents/wio/rules`, first with a config that has
    # no qualified reference and then with `rules_include = ["docs.DOC"]`, and a
    # file system that records the calls it receives
    files = _fs()
    inputs = CheckInputs(ROOT, files)
    plain = make_config(stages={"define": Stage(goal="g")})
    qualified = make_config(stages={"define": _stage("docs.DOC")})

    # When the rule references are checked
    first = diagnostic_lines(selection.check_rule_references(plain, inputs))
    second = diagnostic_lines(selection.check_rule_references(qualified, inputs))

    # Then the first has no diagnostic, the second has the unknown-ruleset error,
    # and `list_dir` was never called
    assert first == []
    assert second == [
        (
            "error: stages.define.rules_include[0]: unknown ruleset `docs`. "
            "No rulesets are declared."
        )
    ]
    assert "list_dir" not in [call for call, _ in files.calls]


def test_an_alias_resolves_like_the_name_of_its_ruleset() -> None:
    """AC-2: an alias works wherever the ruleset's name does."""
    # Given `[rulesets.docs] alias = "d"` over a ruleset directory `docs` and the
    # entry `d.DOC`
    config = make_config(
        stages={"define": _stage("d.DOC")}, rulesets={"docs": Ruleset(alias="d")}
    )

    # When the rule references are checked
    found = list(selection.check_rule_references(config, _docs()))

    # Then the entry passes
    assert found == []


_FIELDS: dict[str, Callable[[str], Config]] = {
    "stages.s.rules_include[0]": lambda ref: make_config(stages={"s": _stage(ref)}),
    "stages.s.rules_exclude[0]": lambda ref: make_config(
        stages={"s": _stage(exclude=(ref,))}
    ),
    "rule_presets.p.rules_include[0]": lambda ref: make_config(
        rule_presets={"p": RulePreset(rules_include=(ref,))}
    ),
    "rule_presets.p.rules_exclude[0]": lambda ref: make_config(
        rule_presets={"p": RulePreset(rules_exclude=(ref,))}
    ),
    "roots.r.rule_presets[0]": lambda ref: make_config(
        roots={"r": Root(paths=("a",), rule_presets=(ref,))}
    ),
    "rules_always_include[0]": lambda ref: make_config(always_include=[ref]),
    "rules_always_exclude[0]": lambda ref: make_config(always_exclude=[ref]),
}


@pytest.mark.parametrize("where", list(_FIELDS))
def test_every_field_that_holds_references_is_judged_at_its_key_path(
    where: str,
) -> None:
    """AC-2: a stage, a config preset, a root and the two always fields."""
    # Given an unknown ruleset in the field at `where`
    config = _FIELDS[where]("zz.DOC")

    # When the rule references are checked
    found = diagnostic_lines(selection.check_rule_references(config, _docs()))

    # Then one error is at `where`
    assert [line.split(": ")[1] for line in found] == [where]


def test_the_first_problem_of_a_reference_in_its_field_wins() -> None:
    """AC-2, AC-4: the form, then what the field takes, then resolution."""
    # Given a veto entry `docz.recommended` with an unknown ruleset, a root entry
    # `docs.DOC001` whose ruleset is known, a root entry `docz.DOC` and `nope`
    known = ["docs"]
    presets = ["mine"]
    judge = selection.judge_reference

    # When the references are judged
    veto = judge("docz.recommended", selection.Takes.VETO, known, presets)
    code = judge("docs.DOC001", selection.Takes.ROOT, known, presets)
    unknown = judge("docz.DOC", selection.Takes.ROOT, known, presets)
    bare = judge("nope", selection.Takes.ROOT, known, presets)

    # Then the first says only qualified codes and families are allowed, since its
    # ruleset part is not the problem, the second says a root takes rule presets
    # only, the third that a root takes rule presets only, and the last lists the
    # config's rule presets
    assert veto is not None
    assert "only qualified codes and families are allowed" in veto
    assert code is not None
    assert "a root takes rule presets only" in code
    assert unknown is not None
    assert "a root takes rule presets only" in unknown
    assert bare == "unknown rule preset `nope`. Declared rule presets: `mine`."


def test_rule_presets_that_include_one_another_are_one_error() -> None:
    """AC-3: one error names the presets of a cycle, and a self loop is one."""
    # Given presets `a` including `b`, `b` including `a`, and `s` including `s`
    config = make_config(
        rule_presets={
            "a": RulePreset(rules_include=("b",)),
            "b": RulePreset(rules_include=("a",)),
            "s": RulePreset(rules_include=("s",)),
        }
    )

    # When the rule presets are checked for cycles
    found = diagnostic_lines(selection.check_rule_preset_cycles(config, _inputs()))

    # Then one error names `a` and `b` at `rule_presets.a.rules_include`, and one
    # names `s` at `rule_presets.s.rules_include`
    assert found == [
        (
            "error: rule_presets.a.rules_include: `a` and `b` include one another; "
            "a cycle has no resolved set."
        ),
        (
            "error: rule_presets.s.rules_include: `s` includes itself; a cycle has no "
            "resolved set."
        ),
    ]


def test_only_a_bare_include_of_a_config_preset_is_an_edge() -> None:
    """AC-3: excludes and qualified references do not make a cycle."""
    # Given a preset `a` that excludes `b` and includes `docs.all`, and `b` that
    # includes `a`
    config = make_config(
        rule_presets={
            "a": RulePreset(rules_include=("docs.all",), rules_exclude=("b",)),
            "b": RulePreset(rules_include=("a",)),
        }
    )

    # When the rule presets are checked for cycles
    found = list(selection.check_rule_preset_cycles(config, _inputs()))

    # Then no error is returned
    assert found == []


def test_a_root_takes_rule_presets_only_and_a_veto_takes_codes_and_families() -> None:
    """AC-4: each field takes only the kinds of name it needs."""
    # Given a ruleset `docs`, a root `wio` with `rule_presets = ["docs.DOC",
    # "docs.all"]`, and `rules_always_exclude = ["docs.recommended", "mine",
    # "docs.DOC001"]` where `mine` is a config rule preset
    config = make_config(
        roots={"wio": Root(paths=("src",), rule_presets=("docs.DOC", "docs.all"))},
        rule_presets={"mine": RulePreset()},
        always_exclude=["docs.recommended", "mine", "docs.DOC001"],
    )

    # When the rule references are checked
    found = diagnostic_lines(selection.check_rule_references(config, _docs()))

    # Then an error at `roots.wio.rule_presets[0]` says a root takes rule presets
    # only, the second entry passes, errors at `rules_always_exclude[0]` and
    # `rules_always_exclude[1]` say only qualified codes and families are allowed
    # there, and the third passes
    assert [line.split(": ")[1] for line in found] == [
        "roots.wio.rule_presets[0]",
        "rules_always_exclude[0]",
        "rules_always_exclude[1]",
    ]
    assert "a root takes rule presets only" in found[0]
    assert all("only qualified codes and families are allowed" in x for x in found[1:])


def test_rulesets_without_a_directory_or_manifest_and_clashing_aliases_fail() -> None:
    """AC-5: each error names the ruleset and what is wrong."""
    # Given `[rulesets.ghost]` with no directory, a directory `bare` without a
    # `ruleset.toml`, two rulesets with the alias `d`, an alias equal to another
    # ruleset's name, and an alias equal to its own ruleset's name
    config = make_config(
        rulesets={
            "ghost": Ruleset(),
            "docs": Ruleset(alias="d"),
            "mine": Ruleset(alias="d"),
            "other": Ruleset(alias="docs"),
            "self": Ruleset(alias="self"),
        }
    )
    inputs = _inputs(
        f"{_RULES}/bare/rule.md",
        *(
            f"{_RULES}/{name}/ruleset.toml"
            for name in ("docs", "mine", "other", "self")
        ),
    )

    # When the rulesets are checked
    found = diagnostic_lines(selection.check_rulesets(config, inputs))

    # Then each but the last is one error that names the ruleset and what is
    # wrong, and the last has none
    assert found == [
        (
            f"error: {_RULES}/bare: `bare` has no `ruleset.toml`; its rules would be "
            "skipped."
        ),
        f"error: rulesets.ghost: `ghost` has no directory under `{_RULES}`.",
        "error: rulesets.mine.alias: alias `d` of `mine` is also the alias of `docs`.",
        (
            "error: rulesets.other.alias: alias `docs` of `other` is also the name "
            "of a ruleset."
        ),
    ]


def test_an_alias_that_is_not_a_ruleset_name_in_form_is_an_error() -> None:
    """AC-1, AC-5: an alias has the form of a ruleset name."""
    # Given a ruleset `docs` with the alias `D`
    config = make_config(rulesets={"docs": Ruleset(alias="D")})

    # When the rulesets are checked
    found = diagnostic_lines(selection.check_rulesets(config, _docs()))

    # Then an error at `rulesets.docs.alias` names the form of a ruleset name
    assert found == [
        (
            "error: rulesets.docs.alias: alias `D` of `docs` is not a ruleset name; a "
            f"ruleset name is {_FORM}."
        )
    ]


def test_a_directory_with_a_malformed_name_is_not_listed_as_a_ruleset() -> None:
    """AC-1, AC-2: a name that no reference could use is not offered."""
    # Given a ruleset `docs` and a directory `Weird` under `.agents/wio/rules`, and
    # the entry `zz.DOC`
    config = make_config(stages={"define": _stage("zz.DOC")})
    inputs = _inputs(f"{_RULES}/docs/ruleset.toml", f"{_RULES}/Weird/ruleset.toml")

    # When the rule references are checked
    found = diagnostic_lines(selection.check_rule_references(config, inputs))

    # Then the declared rulesets leave `Weird` out
    message = "unknown ruleset `zz`. Declared rulesets and aliases: `docs`."
    assert found == [f"error: stages.define.rules_include[0]: {message}"]


def test_an_alias_is_not_known_for_a_table_without_a_directory() -> None:
    """AC-2, AC-5: only a ruleset that has a directory can be named by its alias."""
    # Given a table `ghost` with the alias `g`, which has no directory, and the
    # entry `g.DOC`
    config = make_config(
        stages={"define": _stage("g.DOC")}, rulesets={"ghost": Ruleset(alias="g")}
    )

    # When the rule references are checked
    found = diagnostic_lines(selection.check_rule_references(config, _docs()))

    # Then the entry is an unknown ruleset
    assert found == [
        (
            "error: stages.define.rules_include[0]: unknown ruleset `g`. Declared "
            "rulesets and aliases: `docs`."
        )
    ]


def test_always_included_rules_are_listed_in_a_note() -> None:
    """AC-6: a note tells a driver what every session receives."""
    # Given a ruleset `process` and `rules_always_include =
    # ["process.fix-the-cause"]`, and a config whose `rules_always_include` is
    # empty
    config = make_config(always_include=["process.fix-the-cause"])

    # When the note is made
    found = diagnostic_lines(selection.check_always_include_note(config, _inputs()))
    none = list(selection.check_always_include_note(make_config(), _inputs()))

    # Then a note at `rules_always_include` lists the entry, and the second config
    # has none
    assert found == [
        (
            "note: rules_always_include: every session receives the rules "
            "`process.fix-the-cause`."
        )
    ]
    assert none == []
