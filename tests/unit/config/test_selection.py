# SPDX-License-Identifier: Apache-2.0
"""Tests of the checks of rule references and rulesets."""

import pytest


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("mine", "bare"),
        ("define-bugfix", "bare"),
        ("docs.DOC", "qualified"),
        ("docs.DOC001", "qualified"),
        ("docs.all", "qualified"),
        ("DOC", "malformed: not a rule preset name"),
        ("Docs.DOC", "malformed: the ruleset part"),
        ("docs.Doc1", "malformed: the item"),
        ("docs.DOC001.x", "malformed: more than one dot"),
        ("docs.", "malformed: the item"),
        (".DOC", "malformed: the ruleset part"),
    ],
)
def test_a_reference_has_the_form_of_its_kind(text: str, kind: str) -> None:
    """AC-1: a bare name, a ruleset name and the parts of a qualified reference."""
    # Given a reference as the config writes it
    # When its form is judged
    # Then a bare name and a qualified reference with parts in their forms are
    # told apart, and any other text says which part is wrong and the form it
    # should have
    del text, kind
    pytest.skip("not implemented")


def test_wrong_forms_get_one_error_each_and_no_error_about_a_ruleset() -> None:
    """AC-1: each entry has one error, and the directory `My Rules` another."""
    # Given a stage `define` whose `rules_include` is `["Docs.DOC", "docs.Doc1",
    # "docs.DOC001.x"]`, with a ruleset `docs`, and a directory `My Rules` holding
    # a `ruleset.toml`, under `.agents/wio/rules`
    # When the rule references and the rulesets are checked
    # Then each entry has one error at `stages.define.rules_include[<n>]` that
    # names the form that part should have and none about an unknown ruleset, and
    # the directory has one error at `.agents/wio/rules/My Rules` that names the
    # form of a ruleset name
    pytest.skip("not implemented")


def test_an_unknown_ruleset_and_an_unknown_preset_list_what_exists() -> None:
    """AC-2: the ruleset part must be known, and a bare name a config preset."""
    # Given a stage `define` with `rules_include = ["docz.DOC", "mine",
    # "docs.DOC"]` where there is a ruleset `docs` and no rule preset `mine`
    # When the rule references are checked
    # Then an error at `stages.define.rules_include[0]` names `docz` and lists the
    # rulesets and aliases, one at `stages.define.rules_include[1]` lists the
    # config's rule presets, and the third passes
    pytest.skip("not implemented")


def test_a_root_and_an_always_field_resolve_their_references() -> None:
    """AC-2: a root's `rule_presets` and `rules_always_include` are judged."""
    # Given a root `wio` with `rule_presets = ["docz.all"]`, where there is no
    # ruleset or alias `docz`, and `rules_always_include = ["nope"]`
    # When the rule references are checked
    # Then an error at `roots.wio.rule_presets[0]` names `docz` and one at
    # `rules_always_include[0]` lists the config's rule presets
    pytest.skip("not implemented")


def test_no_rules_directory_is_asked_about_before_it_is_listed() -> None:
    """AC-2: a repository without `.agents/wio/rules` has no ruleset and no error."""
    # Given a repository without `.agents/wio/rules`, first with a config that has
    # no qualified reference and then with `rules_include = ["docs.DOC"]`, and a
    # file system that records the calls it receives
    # When the rule references are checked
    # Then the first has no diagnostic, the second has the unknown-ruleset error,
    # and `list_dir` was never called
    pytest.skip("not implemented")


def test_an_alias_resolves_like_the_name_of_its_ruleset() -> None:
    """AC-2: an alias works wherever the ruleset's name does."""
    # Given `[rulesets.docs] alias = "d"` over a ruleset directory `docs` and the
    # entry `d.DOC`
    # When the rule references are checked
    # Then the entry passes
    pytest.skip("not implemented")


def test_rule_presets_that_include_one_another_are_one_error() -> None:
    """AC-3: one error names the presets of a cycle, and a self loop is one."""
    # Given presets `a` including `b`, `b` including `a`, and `s` including `s`
    # When the rule presets are checked for cycles
    # Then one error names `a` and `b` at `rule_presets.a.rules_include`, and one
    # names `s` at `rule_presets.s.rules_include`
    pytest.skip("not implemented")


def test_only_a_bare_include_of_a_config_preset_is_an_edge() -> None:
    """AC-3: excludes and qualified references do not make a cycle."""
    # Given a preset `a` that excludes `b` and includes `docs.all`, and `b` that
    # includes `a`
    # When the rule presets are checked for cycles
    # Then no error is returned
    pytest.skip("not implemented")


def test_a_root_takes_rule_presets_only_and_a_veto_takes_codes_and_families() -> None:
    """AC-4: each field takes only the kinds of name it needs."""
    # Given a ruleset `docs`, a root `wio` with `rule_presets = ["docs.DOC",
    # "docs.all"]`, and `rules_always_exclude = ["docs.recommended", "mine",
    # "docs.DOC001"]` where `mine` is a config rule preset
    # When the rule references are checked
    # Then an error at `roots.wio.rule_presets[0]` says a root takes rule presets
    # only, the second entry passes, errors at `rules_always_exclude[0]` and
    # `rules_always_exclude[1]` say only qualified codes and families are allowed
    # there, and the third passes
    pytest.skip("not implemented")


def test_rulesets_without_a_directory_or_manifest_and_clashing_aliases_fail() -> None:
    """AC-5: each error names the ruleset and what is wrong."""
    # Given `[rulesets.ghost]` with no directory, a directory `bare` without a
    # `ruleset.toml`, two rulesets with the alias `d`, and an alias equal to
    # another ruleset's name
    # When the rulesets are checked
    # Then each is an error that names the ruleset and what is wrong
    pytest.skip("not implemented")


def test_an_alias_that_is_not_a_ruleset_name_in_form_is_an_error() -> None:
    """AC-1, AC-5: an alias has the form of a ruleset name."""
    # Given a ruleset `docs` with the alias `D`
    # When the rulesets are checked
    # Then an error at `rulesets.docs.alias` names the form of a ruleset name
    pytest.skip("not implemented")


def test_always_included_rules_are_listed_in_a_note() -> None:
    """AC-6: a note tells a driver what every session receives."""
    # Given a ruleset `process` and `rules_always_include =
    # ["process.fix-the-cause"]`, and a config whose `rules_always_include` is
    # empty
    # When the note is made
    # Then a note at `rules_always_include` lists the entry, and the second config
    # has none
    pytest.skip("not implemented")
