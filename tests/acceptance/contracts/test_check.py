# SPDX-License-Identifier: Apache-2.0
"""Scenario stubs of `wio contracts check`.

Each stub is one scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario and its fixture.
"""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

# The implementation stage adds the sample repositories under
# `tests/fixtures/contracts`, one for each project of the scenarios below, each
# with a config that declares what the project needs and, for AC-4 and AC-5, the
# templates that it names. AC-7 reads a Work file a second time and fails, which
# no process shows, so its second scenario is a unit test.

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_check_reports_every_problem_at_once_and_exits_by_severity(wio: Wio) -> None:
    """AC-1: scenario of the contract."""
    # Given a project whose defaults have `deliver`, with a shared id, a cycle,
    # an unknown key and a missing template
    # When `wio contracts check` runs, as text and with `--json`
    # Then both report the four in the order of `order_diagnostics`, the second
    # as one array, and each exits 1
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_clean_tree_passes_and_a_warning_does_not_fail(wio: Wio) -> None:
    """AC-1: scenario of the contract."""
    # Given a clean tree and a tree whose only problem is a warning
    # When `wio contracts check` runs on each
    # Then the first prints `The contracts pass.`, the second the warning, and
    # each exits 0
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_mistyped_key_is_told_by_its_closest_known_key(wio: Wio) -> None:
    """AC-2: scenario of the contract."""
    # Given Works with unknown keys, a plain `x`, the table `[xx]`, and with the
    # table `[x]` and the key `tracks`
    # When `wio contracts check` runs
    # Then the warnings of the contract are reported at the files and the second
    # group gives none
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_an_id_that_would_break_a_record_is_an_error(wio: Wio) -> None:
    """AC-3: scenario of the contract."""
    # Given five Works with the ids of the contract
    # When `wio contracts check` runs
    # Then the three bad ids are errors with their messages
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_missing_and_a_rejected_template_are_told_apart(wio: Wio) -> None:
    """AC-4: scenario of the contract."""
    # Given Works that name `nosuch`, `bad` and `unclosed`, and one that names none
    # When `wio contracts check` runs
    # Then the errors of the contract are reported and a Work with a template
    # error is not told it has no action
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_repeat_that_a_work_inherits_is_reported_at_its_own_file(wio: Wio) -> None:
    """AC-5: scenario of the contract."""
    # Given the config of the previous scenario, a template whose action repeats
    # a stage and a Work that follows it and names no action
    # When `wio contracts check` runs
    # Then the repeat is an error at the Work's file
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_actions_a_work_names_exist_and_it_has_some(wio: Wio) -> None:
    """AC-5: scenario of the contract."""
    # Given the config of the contract and Works whose `[actions]` hold the
    # faults of the contract
    # When `wio contracts check` runs
    # Then each fault is reported as the contract words it, and a Work that
    # follows a template with a repeat is told at its own file
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_work_that_resolves_to_no_action_is_an_error(wio: Wio) -> None:
    """AC-5: scenario of the contract."""
    # Given three projects: no defaults, a template whose only action is
    # removed, and defaults
    # When `wio contracts check` runs in each
    # Then the first two report that the Work resolves to no action, the third nothing
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_roots_a_work_names_exist(wio: Wio) -> None:
    """AC-6: scenario of the contract."""
    # Given a nesting project with an undeclared root, a leaf with
    # `@descendants` and a parent that leaves out roots
    # When `wio contracts check` runs
    # Then the error, the warning and the two notes are reported and the exit code is 1
    raise NotImplementedError


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_several_problems_of_one_work_are_all_reported_once(wio: Wio) -> None:
    """AC-7: scenario of the contract."""
    # Given Works with several problems each, a wrong `roots` and a wrong `template`
    # When `wio contracts check` runs
    # Then each finding is reported once and the skipped ones are not
    raise NotImplementedError
