# SPDX-License-Identifier: Apache-2.0
"""Test stubs of the check of the Works.

Each stub is a scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


def test_a_missing_and_a_rejected_template_are_told_apart() -> None:
    """AC-4: scenario of the contract."""
    # Given Works that name a missing template, a rejected one and none
    # When the Works are checked
    # Then each of the first two is an error that names the template, the second
    # pointing to `wio templates check`, and no Work with a template error is
    # told it has no action
    raise NotImplementedError


def test_the_names_of_a_works_own_actions_must_be_declared() -> None:
    """AC-5: scenario of the contract."""
    # Given a config that declares actions, a stage preset and a stage, and
    # Works whose `[actions]` name an undeclared action, preset and stage, a
    # stage twice and an empty list
    # When the Works are checked
    # Then the first four are errors with their messages and the empty list is
    # not one, because another action remains
    raise NotImplementedError


def test_a_repeat_that_a_work_inherits_from_its_template_is_reported_at_the_work() -> (
    None
):
    """AC-5: scenario of the contract."""
    # Given a template whose action repeats a stage and a Work that follows it
    # with no actions of its own
    # When the Work is checked
    # Then the repeat is an error at the Work's file
    raise NotImplementedError


def test_a_work_that_resolves_to_no_action_is_an_error() -> None:
    """AC-5: scenario of the contract."""
    # Given a project with no defaults, one whose Work removes the only action
    # of its template, and one with defaults
    # When each Work is checked
    # Then the first two give `The Work resolves to no action` and the third nothing
    raise NotImplementedError


def test_a_root_that_the_config_does_not_declare_is_an_error() -> None:
    """AC-6: scenario of the contract."""
    # Given a nesting tree with an undeclared root, a leaf that lists
    # `@descendants` and a parent that leaves out roots of its children
    # When the Works are checked
    # Then the error, the warning and one note for each omitted root are
    # reported, and `@descendants` is no root
    raise NotImplementedError


def test_every_concern_is_checked_for_every_work_once() -> None:
    """AC-7: scenario of the contract."""
    # Given a Work with an unknown key, an undeclared root and an undeclared
    # action, a parent with a wrong `roots` and a Work with `template = 1`
    # When the Works are checked
    # Then each gets its findings once, the parent no finding about roots and no
    # note, and the Work with the wrong template no `resolves to no action`
    raise NotImplementedError


def test_a_file_that_cannot_be_read_again_is_one_error_and_a_template_is_skipped() -> (
    None
):
    """AC-7: scenario of the contract."""
    # Given a file system that fails the second read of a Work and a template
    # that fails on the read of its `[actions]`
    # When the Works are checked
    # Then the first Work has one error at its file and the Works of the
    # template give no diagnostic
    raise NotImplementedError


def test_the_findings_of_discovery_and_the_graph_are_carried_through_once() -> None:
    """AC-1: scenario of the contract."""
    # Given a shared id and a cycle
    # When the Works are checked
    # Then each is reported once, as discovery and the hierarchy word it
    raise NotImplementedError


def test_the_command_writes_the_findings_and_exits_by_severity() -> None:
    """AC-1: scenario of the contract."""
    # Given findings of each severity
    # When the command runs, as text and with `--json`
    # Then it exits 1 for an error and 0 for a warning or a note, and says that
    # the contracts pass when there is nothing
    raise NotImplementedError


def test_a_note_for_an_omitted_root_is_given_even_when_it_is_not_declared() -> None:
    """AC-6: constraint of the contract."""
    # Given a parent whose child names a root that the config does not declare
    # When the Works are checked
    # Then the child gets the error for the root and the parent a note for it
    raise NotImplementedError


def test_under_flat_a_work_that_lists_descendants_is_warned() -> None:
    """AC-6: constraint of the contract."""
    # Given `flat` and a Work that lists `@descendants`
    # When the Works are checked
    # Then it gets the warning that it has no children
    raise NotImplementedError


def test_a_template_is_read_once_however_many_works_follow_it() -> None:
    """AC-7: scenario of the contract."""
    # Given three Works that follow one template, and a file system that counts
    # its reads
    # When the Works are checked
    # Then the template's file was read once, and each Work's file once more
    raise NotImplementedError


def test_a_work_whose_actions_discovery_reported_is_not_resolved() -> None:
    """Constraint: a field that discovery reported is not resolved."""
    # Given a Work whose `[actions]` is a string, which discovery reported
    # When the Works are checked
    # Then the error of discovery is all it gets about its actions
    raise NotImplementedError


def test_a_work_with_a_missing_template_still_has_its_own_names_checked() -> None:
    """Constraint: only the resolved checks are skipped."""
    # Given a Work that names a missing template and an undeclared action
    # When the Works are checked
    # Then it gets the error for the template and the error for the action, and
    # none about resolving
    raise NotImplementedError


def test_the_marker_of_the_block_is_not_an_unknown_key() -> None:
    """Constraint: the `wio` marker is not a key."""
    # Given Works with a `<!-- wio` block and with a `+++` block
    # When the Works are checked
    # Then neither is told that `wio` is an unknown key
    raise NotImplementedError
