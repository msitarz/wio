# SPDX-License-Identifier: Apache-2.0
"""Test stubs of the check of the Works.

Each stub is a scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


def test_an_unknown_key_is_a_warning_with_its_closest_known_key() -> None:
    """AC-2: scenario of the contract."""
    # Given Works with the keys `depend_on`, `zzz`, a plain `x` and the table
    # `[xx]`, and Works with the table `[x]` and the key `tracks`
    # When the Works are checked
    # Then the first four give a warning at the file, the first with `Did you
    # mean `depends_on`?`, and the second group gives nothing
    raise NotImplementedError


def test_an_id_that_would_break_a_record_is_an_error() -> None:
    """AC-3: scenario of the contract."""
    # Given Works with the ids `a b`, `a,b`, `none`, `SPEC-012` and `k3m9xq`
    # When the Works are checked
    # Then the first three are errors with their messages and the last two give nothing
    raise NotImplementedError


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
