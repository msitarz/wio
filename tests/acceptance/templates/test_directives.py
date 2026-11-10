# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio templates directives`, which prints the directive grammar."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_directives_prints_the_table_for_a_person(wio: Wio) -> None:
    """AC-1: one block for each entry of the table, in its order, exit 0."""
    # Given any working directory and the table
    # When `wio templates directives` runs
    # Then it prints exactly one block for each entry in order, with empty
    # standard error, and exits 0


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_directives_json_prints_the_table_as_one_array(wio: Wio) -> None:
    """AC-2: `--json` prints one array in the table's order with its fields."""
    # Given any working directory and the table
    # When `wio templates directives --json` runs
    # Then the output is one array with an object for each entry in order, empty
    # standard error, and exit 0


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.channels(Channel.CLI)
def test_directives_works_outside_a_repository_and_with_a_broken_project(
    wio: Wio,
) -> None:
    """AC-3: the same output with no repository, a bad config or no templates."""
    # Given a directory outside any repository, a repository whose config has an
    # error, one with no config file and one whose templates directory is
    # unreadable
    # When `wio templates directives` runs in each
    # Then all four print the same text, in both forms, as anywhere else, with
    # empty standard error, and exit 0


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_directives_prints_the_same_text_on_every_run(wio: Wio) -> None:
    """AC-7: each form is identical twice."""
    # Given any working directory
    # When `directives` and `directives --json` each run twice
    # Then the two outputs of each command are identical


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.channels(Channel.CLI)
def test_directives_with_an_extra_argument_is_a_usage_mistake(wio: Wio) -> None:
    """AC-5: `directives extra` exits 2, and the help of `wio templates` names it."""
    # Given any working directory
    # When `wio templates directives extra` runs, and then `wio templates`
    # Then the first exits 2 with a usage message, and the help names
    # `directives`
