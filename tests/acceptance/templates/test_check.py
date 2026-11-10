# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio templates check`, which reports every template problem."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

SKIP = "Pending the implementation stage."


@pytest.mark.skip(reason=SKIP)
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_says_that_a_project_passes(wio: Wio) -> None:
    """AC-1: the text says so, the JSON is `[]`, and both exit 0."""
    # Given a project whose templates have no problem
    # When `wio templates check` and `wio templates check --json` run
    # Then the first says that the templates pass and the second prints `[]`,
    # each exiting 0; so does a project with no templates


@pytest.mark.skip(reason=SKIP)
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_prints_two_problems_at_once(wio: Wio) -> None:
    """AC-1: both problems are printed in order, as text and as JSON, exit 1."""
    # Given a project with an unknown key in one template and a wrong directive
    # in another
    # When `wio templates check` and `wio templates check --json` run
    # Then the first prints both as `<severity>: <where>: <message>` lines and
    # the second one array of two objects, in that order, each exiting 1


@pytest.mark.skip(reason=SKIP)
@pytest.mark.channels(Channel.CLI)
def test_check_refuses_a_config_with_an_error(wio: Wio) -> None:
    """AC-1: the config's error is printed and the exit code is 2."""
    # Given a project whose config has an error
    # When `wio templates check` runs
    # Then it prints that error and exits 2


@pytest.mark.skip(reason=SKIP)
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_reports_what_discovery_finds(wio: Wio) -> None:
    """AC-2: an unclosed block, a duplicate name and a missing directory."""
    # Given a project with a comment block that does not close and two files
    # named `a.md`, and one whose templates directory is missing
    # When `wio templates check` runs on each
    # Then the first prints an error for the block and one for the duplicate,
    # naming the files, and the second one error that names the directory and
    # none for the entry template, each exiting 1


@pytest.mark.skip(reason=SKIP)
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_reports_unknown_keys(wio: Wio) -> None:
    """AC-3: four errors that name the file and the key, none for `[contract]`."""
    # Given templates with `name`, `descriptions`, `contract = 1`, `actions = 1`
    # and a `[contract]` that holds `ticket = ""`
    # When `wio templates check` runs
    # Then the first four each give an error that names the file and the key,
    # and the last gives none


@pytest.mark.skip(reason=SKIP)
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_names_the_line_and_column_of_a_directive_error(wio: Wio) -> None:
    """AC-4: the places are `<file>:12:16`, `<file>:14:6` and `<file>:16:7`."""
    # Given a template with a refused list on line 12, an unclosed one on line 14
    # and a list on a level-3 heading on line 16
    # When `wio templates check` runs
    # Then it prints an error for each at those places


@pytest.mark.skip(reason=SKIP)
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_reports_names_the_config_does_not_declare(wio: Wio) -> None:
    """AC-5: undeclared names and wrong value types are errors, empty is not."""
    # Given a config declaring the action `define`, the stage preset
    # `define-feature` and the stage `implementation`, and templates whose
    # `[actions]` hold `define = "nosuch"`, `nosuch = "define-feature"`,
    # `define = ["nosuch"]`, `define = 1`, `define = [1]`, `define = []` and
    # `define = ["implementation"]`
    # When `wio templates check` runs
    # Then the first three name the file and the undeclared name, the next two
    # name the file and the key `define`, and the last two give none


@pytest.mark.skip(reason=SKIP)
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_reports_a_kind_that_disagrees_with_the_config(wio: Wio) -> None:
    """AC-6: an undeclared kind, a missing entry and an entry of another kind."""
    # Given the kinds `feature = "feature.draft"` and `bugfix = "missing"`, a
    # template `feature.draft` of kind `bugfix`, and a template `other` of kind
    # `nokind`
    # When `wio templates check` runs
    # Then it prints the three errors at their places and exits 1


@pytest.mark.skip(reason=SKIP)
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_warns_of_a_repeated_heading_and_still_passes(wio: Wio) -> None:
    """AC-7: a warning at the second heading, and the exit code is 0."""
    # Given a template with `## Goals <!-- wio: required -->` and `## goals`
    # When `wio templates check` runs
    # Then it prints a warning at the second heading that names the first
    # line, and exits 0
