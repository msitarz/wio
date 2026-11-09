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
    # Then it prints one error for each entry and one for the directory, exits 1
    del wio
    pytest.skip("not implemented")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_every_reference_resolves_to_a_ruleset_or_a_preset(wio: Wio) -> None:
    """AC-2: an unknown ruleset or preset is an error that lists what exists."""
    # Given the config `rules-resolve` with an unknown ruleset, an unknown rule
    # preset and an alias that resolves, and `rules-resolve-none` without
    # `.agents/wio/rules` and without a qualified reference
    # When `wio config check` runs on each
    # Then the first prints the two errors and exits 1, the second prints nothing
    del wio
    pytest.skip("not implemented")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_rule_presets_do_not_form_a_cycle(wio: Wio) -> None:
    """AC-3: a cycle is one error that names the presets on it."""
    # Given the config `rules-cycles` with rule presets that include one another
    # and one that includes itself
    # When `wio config check` runs
    # Then it prints one error for each cycle and exits 1
    del wio
    pytest.skip("not implemented")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_each_field_takes_only_the_kinds_of_name_it_needs(wio: Wio) -> None:
    """AC-4: a family in a root and a preset in the veto are errors."""
    # Given the config `rules-kinds` with a family in a root's `rule_presets` and
    # a preset in `rules_always_exclude`
    # When `wio config check` runs
    # Then it prints an error for each and exits 1
    del wio
    pytest.skip("not implemented")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_rulesets_and_aliases_are_consistent(wio: Wio) -> None:
    """AC-5: a missing directory, a missing manifest and a clashing alias fail."""
    # Given the config `rules-rulesets` with a `[rulesets]` table without a
    # directory, a directory without a `ruleset.toml` and clashing aliases
    # When `wio config check` runs
    # Then it prints an error for each and exits 1
    del wio
    pytest.skip("not implemented")


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_note_lists_what_every_session_gets(wio: Wio) -> None:
    """AC-6: a note lists `rules_always_include` and the command exits 0."""
    # Given the config `rules-note` with `rules_always_include =
    # ["process.fix-the-cause"]` over a ruleset `process`
    # When `wio config check` runs
    # Then it prints a note that lists the entry and exits 0
    del wio
    pytest.skip("not implemented")
