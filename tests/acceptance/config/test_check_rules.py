# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio config check` on the rule references and the rulesets."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_names_have_the_form_of_their_kind(wio: Wio) -> None:
    """AC-1: a wrong form is an error that names the form."""
    # Given the config `rules-forms` with references of wrong forms and a
    # directory `My Rules`
    # When `wio config check` runs
    output = wio.check_config("rules-forms")

    # Then it prints one error for each entry and one for the directory, exits 1
    assert [line.split(": ")[1] for line in output.lines] == [
        ".agents/wio/rules/My Rules",
        "stages.define.rules_include[0]",
        "stages.define.rules_include[1]",
        "stages.define.rules_include[2]",
    ]
    assert all(line.startswith("error: ") for line in output.lines)
    assert output.exit_code == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_every_reference_resolves_to_a_ruleset_or_a_preset(wio: Wio) -> None:
    """AC-2: an unknown ruleset or preset is an error that lists what exists."""
    # Given the config `rules-resolve` with an unknown ruleset, an unknown rule
    # preset and an alias that resolves, and `rules-resolve-none` without
    # `.agents/wio/rules` and without a qualified reference
    # When `wio config check` runs on each
    unknown = wio.check_config("rules-resolve")
    none = wio.check_config("rules-resolve-none")

    # Then the first prints the errors and exits 1, the second prints nothing
    assert [line.split(": ")[1] for line in unknown.lines] == [
        "roots.wio.rule_presets[0]",
        "stages.define.rules_include[0]",
        "stages.define.rules_include[1]",
    ]
    assert "Declared rulesets and aliases: `d`, `docs`." in unknown.lines[0]
    assert unknown.exit_code == 1
    assert none.lines == ["Config check passed!"]
    assert none.exit_code == 0


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_rule_presets_do_not_form_a_cycle(wio: Wio) -> None:
    """AC-3: a cycle is one error that names the presets on it."""
    # Given the config `rules-cycles` with rule presets that include one another
    # and one that includes itself
    # When `wio config check` runs
    output = wio.check_config("rules-cycles")

    # Then it prints one error for each cycle and exits 1
    assert [line.split(": ")[1] for line in output.lines] == [
        "rule_presets.a.rules_include",
        "rule_presets.s.rules_include",
    ]
    assert "`a` and `b`" in output.lines[0]
    assert output.exit_code == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_each_field_takes_only_the_kinds_of_name_it_needs(wio: Wio) -> None:
    """AC-4: a family in a root and a preset in the veto are errors."""
    # Given the config `rules-kinds` with a family in a root's `rule_presets` and
    # a preset in `rules_always_exclude`
    # When `wio config check` runs
    output = wio.check_config("rules-kinds")

    # Then it prints an error for each and exits 1
    assert [line.split(": ")[1] for line in output.lines] == [
        "roots.wio.rule_presets[0]",
        "rules_always_exclude[0]",
        "rules_always_exclude[1]",
    ]
    assert output.exit_code == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_rulesets_and_aliases_are_consistent(wio: Wio) -> None:
    """AC-5: a missing directory, a missing manifest and a clashing alias fail."""
    # Given the config `rules-rulesets` with a `[rulesets]` table without a
    # directory, a directory without a `ruleset.toml` and clashing aliases
    # When `wio config check` runs
    output = wio.check_config("rules-rulesets")

    # Then it prints an error for each and exits 1
    assert [line.split(": ")[1] for line in output.lines] == [
        ".agents/wio/rules/bare",
        "rulesets.ghost",
        "rulesets.mine.alias",
        "rulesets.other.alias",
    ]
    assert output.exit_code == 1


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_note_lists_what_every_session_gets(wio: Wio) -> None:
    """AC-6: a note lists `rules_always_include` and the command exits 0."""
    # Given the config `rules-note` with `rules_always_include =
    # ["process.fix-the-cause"]` over a ruleset `process`
    # When `wio config check` runs
    output = wio.check_config("rules-note")

    # Then it prints a note that lists the entry and exits 0
    assert len(output.lines) == 1
    assert output.lines[0].startswith("note: rules_always_include: ")
    assert "`process.fix-the-cause`" in output.lines[0]
    assert output.exit_code == 0
