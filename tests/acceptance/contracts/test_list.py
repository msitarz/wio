# SPDX-License-Identifier: Apache-2.0
"""Scenario stubs of `wio contracts list`.

Each stub is one scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario and its fixture.
"""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

# The implementation stage adds the sample repositories under
# `tests/fixtures/contracts`: `list-nesting` (AC-1, AC-3, AC-6), `list-flat`
# (AC-2, AC-3), `list-empty` (AC-4), `list-shared-id` and `list-unreadable`
# (AC-5, the latter with a file that is not UTF-8) and `list-soft-errors` (AC-5).
# AC-6 needs a DSL verb that fingerprints the contract files of the sandbox,
# which both drivers answer from the directory they run in.

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_works_are_listed_with_their_hierarchy_and_their_overrides(
    wio: Wio,
) -> None:
    """AC-1: scenario of the contract."""
    # Given a nesting project with a parent and three children
    # When `wio contracts list` runs
    # Then it prints the text of AC-1 and exits 0
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_under_flat_every_work_is_at_the_same_indent(wio: Wio) -> None:
    """AC-2: scenario of the contract."""
    # Given a flat project with three Works
    # When `wio contracts list` runs
    # Then it prints the text of AC-2 and exits 0
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_json_is_one_array_with_the_same_facts(wio: Wio) -> None:
    """AC-3: scenario of the contract."""
    # Given the two projects above
    # When `wio contracts list --json` runs on each
    # Then each prints one line that parses to the objects of AC-3
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_tree_with_no_work_prints_nothing(wio: Wio) -> None:
    """AC-4: scenario of the contract."""
    # Given a repository with no Work
    # When `list` and `list --json` run
    # Then the first prints nothing, the second `[]`, and each exits 0
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_an_incomplete_tree_refuses_the_listing(wio: Wio) -> None:
    """AC-5: scenario of the contract."""
    # Given a tree with a shared id and a tree with an unreadable Work file
    # When `list` and `list --json` run on each
    # Then each writes nothing to standard output, the errors and the hint to
    # standard error, and exits 2
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_errors_that_do_not_leave_the_tree_incomplete_do_not_refuse(wio: Wio) -> None:
    """AC-5: scenario of the contract."""
    # Given an undeclared root, a root of the wrong type and two Works that list
    # each other
    # When `wio contracts list` runs
    # Then all four are listed and the exit code is 0
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_listing_writes_nothing_and_prints_the_same_bytes_twice(wio: Wio) -> None:
    """AC-6: scenario of the contract."""
    # Given the Works of AC-1 and a hash of each contract
    # When `list` and `list --json` each run twice
    # Then the outputs of each are identical and no contract changed
    raise NotImplementedError
