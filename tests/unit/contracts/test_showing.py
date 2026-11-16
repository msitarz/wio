# SPDX-License-Identifier: Apache-2.0
"""Test stubs of how `show` finds a Work and its actions.

Each stub is a scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario and its fixture.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


def test_an_argument_with_a_slash_or_a_md_ending_is_a_path_and_any_other_is_an_id() -> (
    None
):
    """AC-3: path or id."""
    # Given Works and the arguments `p/c/README.md`, `notes.md`, `k3m9xq` and an
    # id written `a/b`
    # When `find_target` runs on each
    # Then the first two are looked up as paths, `k3m9xq` as an id, and `a/b`
    # cannot be an id
    raise NotImplementedError


def test_a_relative_path_is_resolved_against_the_working_directory() -> None:
    """AC-3: a path from a subdirectory."""
    # Given the Works of AC-1 and the working directory `.agents/wio/works/p`
    # When `find_target` runs on `c/README.md`
    # Then it gives the Work `k3m9xq`
    raise NotImplementedError


def test_an_unknown_id_names_itself_and_the_closest_id_when_there_is_one() -> None:
    """AC-3: an id that no Work has."""
    # Given the Works of AC-1
    # When `find_target` runs on `k3m9xr` and `zzzzzz`
    # Then the first raises ``No Work has the id `k3m9xr`. Did you mean
    # `k3m9xq`?`` and the second the same without the question
    raise NotImplementedError


def test_a_shared_id_refuses_only_its_own_lookup() -> None:
    """AC-3: a shared id."""
    # Given two Works with the id `a7b2c4` and a Work that lists it
    # When `find_target` runs on `a7b2c4` and on the other Work
    # Then the first raises the error of discovery and the other Work is found
    raise NotImplementedError


def test_a_file_that_is_not_a_work_gives_the_reason_of_discovery() -> None:
    """AC-3: a file that is not a Work."""
    # Given an unmarked file, a path that does not exist and a file outside the
    # Works directory
    # When `find_target` runs on each
    # Then each raises an error that names the path and a different reason
    raise NotImplementedError


def test_the_actions_follow_the_config_then_the_names_it_does_not_declare() -> None:
    """AC-1: actions in the order of the config."""
    # Given a config declaring `define`, `deliver` and `amend`, a template that
    # gives an undeclared `ratify` and a Work whose own `[actions]` give an
    # undeclared `deploy`
    # When `shown_actions` runs
    # Then the declared actions come first in the config's order, then `deploy`,
    # which the Work lists, and then `ratify`, as written
    raise NotImplementedError


def test_the_defaults_apply_only_without_a_template_and_own_actions_replace() -> None:
    """AC-1: defaults and an override."""
    # Given a Work with no template and one with a template, both with
    # `[works.defaults.actions]`
    # When `shown_actions` runs on each
    # Then the first has the defaults and the second only its template, each
    # with the Work's own replacing them, and the sources say which
    raise NotImplementedError


def test_an_emptied_action_is_removed_and_an_empty_one_is_not_shown() -> None:
    """AC-1: removed and empty actions."""
    # Given a template with `amend` and a Work whose `[actions]` empty `amend`
    # and `ratify`
    # When `shown_actions` runs
    # Then `amend` is removed with the source `contract` and `ratify` is not
    # shown
    raise NotImplementedError


def test_a_work_with_nothing_to_resolve_has_no_action() -> None:
    """AC-1: a Work that resolves to no action."""
    # Given a config with no defaults and a Work with no template and no
    # `[actions]`
    # When `shown_actions` runs
    # Then it gives no action
    raise NotImplementedError


def test_a_template_the_catalog_lacks_or_rejects_gives_no_actions() -> None:
    """AC-1: a template that cannot be used."""
    # Given a Work whose template is missing from the catalog, one whose
    # template is rejected and one whose template file cannot be read
    # When `shown_actions` runs on each
    # Then only the Work's own actions are given
    raise NotImplementedError


def test_a_preset_the_config_does_not_declare_is_kept_with_no_stages() -> None:
    """AC-5: an undeclared preset."""
    # Given a Work whose action names a stage preset that the config does not
    # declare
    # When `shown_actions` runs
    # Then the action has the preset as written and no stages
    raise NotImplementedError


def test_related_works_are_found_by_id_and_a_missing_or_shared_id_is_told() -> None:
    """AC-3: related works."""
    # Given a Work that lists a missing id, an id of a Work with no title and an
    # id that two Works share
    # When `gather_work` runs
    # Then the missing id is not found, the untitled Work has no title and the
    # shared id is once for each Work
    raise NotImplementedError


def test_the_resolved_roots_and_the_dependents_come_from_the_hierarchy() -> None:
    """AC-2: roots and dependents."""
    # Given a parent that lists `@descendants` and two Works that list a sibling
    # When `gather_work` runs on the parent and on the sibling
    # Then the parent's resolved roots are those of its children and the sibling
    # has both dependents
    raise NotImplementedError


def test_an_incomplete_tree_refuses_the_command_before_the_argument_is_looked_up() -> (
    None
):
    """AC-4: an incomplete tree."""
    # Given a tree with a Work left out and a good Work
    # When `run_show` runs on the good Work
    # Then nothing is written to standard output and the error and the hint are
    # raised
    raise NotImplementedError
