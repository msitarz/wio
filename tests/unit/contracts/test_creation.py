# SPDX-License-Identifier: Apache-2.0
"""Test stubs of the creation of a Work.

Each stub is a scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


def test_a_work_is_created_from_the_entry_template_of_a_kind() -> None:
    """AC-1: scenario of the contract."""
    # Given a config with the kind `feature` whose entry template has a
    # `[contract]` table, the root `wio`, and an Entropy that gives the bytes
    # 19, 3, 20, 9, 29 and 23
    # When the Work is planned with `--title Read config --root wio` and reported
    # Then the file has the values and body of the contract and the report names
    # the id and the path
    raise NotImplementedError


def test_any_template_can_be_used_and_kind_and_template_must_agree() -> None:
    """AC-2: scenario of the contract."""
    # Given two kinds, a leaf template with roots, a parent Work under nesting
    # When Works are planned with a template and a parent, with a template and
    # no kind, and with a template of another kind
    # Then the first is under the parent with the leaf's roots, the second is
    # from the leaf, and the third is an error naming the other kind
    raise NotImplementedError


def test_a_bare_contract_holds_the_id_and_a_heading() -> None:
    """AC-3: scenario of the contract."""
    # Given an empty tree under nesting
    # When bare contracts are planned with a slug, a title and a path
    # Then the file holds the block with the id, an empty line and the heading,
    # one line feed each
    raise NotImplementedError


def test_the_block_is_edited_and_nothing_else_is() -> None:
    """AC-4: scenario of the contract."""
    # Given front matter, plain and CRLF templates, with roots given twice
    # When Works are planned from them
    # Then the keys and table have the requested values and CRLF is kept throughout
    raise NotImplementedError


def test_a_title_replaces_the_first_heading_or_is_inserted() -> None:
    """AC-4: scenario of the contract."""
    # Given templates with a title, with no title and with CRLF and no title
    # When Works are planned with a title and without
    # Then the heading is replaced, inserted before the first line of the body
    # that is not empty, or left out, with the template's line ending
    raise NotImplementedError


def test_roots_are_a_set_of_declared_names() -> None:
    """AC-4: scenario of the contract."""
    # Given a config declaring `api` and `web`
    # When roots are given twice, in another order, and `@descendants`
    # Then each counts once in the order of its first appearance, and an
    # undeclared one is an error
    raise NotImplementedError


def test_each_mistake_is_one_error_that_says_what_to_do() -> None:
    """AC-5: scenario of the contract."""
    # Given a config with no kinds, an entry template that is missing, one that
    # is rejected, and a name that no file has
    # When Works are planned
    # Then each is its own error with its own pointer to `wio templates check`
    # or `wio templates list`
    raise NotImplementedError


def test_a_rejected_template_given_by_name_is_an_error() -> None:
    """AC-5: scenario of the contract."""
    # Given a template that `wio templates check` rejects
    # When a Work is planned from it by name
    # Then the error says it is rejected and points to `wio templates check`
    raise NotImplementedError


def test_only_the_first_of_several_mistakes_is_reported() -> None:
    """AC-5: scenario of the contract."""
    # Given two mistakes at once: kind and root, root and an existing directory,
    # a blank title, a title with a line break, and an unknown parent
    # When Works are planned
    # Then each reports only its first mistake in the order of the contract
    raise NotImplementedError


def test_a_write_that_fails_reports_nothing() -> None:
    """AC-5: scenario of the contract."""
    # Given a file system that reports the path free to the decision and
    # existing to the guard
    # When the command runs
    # Then it is an error that names the path, nothing is written to standard
    # output and no file is created
    raise NotImplementedError


def test_the_report_is_one_object_with_the_same_facts() -> None:
    """AC-6: scenario of the contract."""
    # Given a parent Work, and the config and templates of the contract
    # When reports are written as JSON for a template under a parent, a bare
    # contract and a path under nesting
    # Then each object has the fields in order, with `null` for none and the
    # parent from the place
    raise NotImplementedError


def test_the_human_report_names_the_id_the_title_and_the_path() -> None:
    """AC-1: scenario of the contract."""
    # Given a Work with a title and one with none
    # When they are reported as text
    # Then the first line has the id and the title or `(no title)`, and the path
    # follows indented by two
    raise NotImplementedError


def test_new_sets_the_id_and_the_roots_through_the_one_function() -> None:
    """AC-7: scenario of the contract."""
    # Given a stand-in for `set_block_keys` that records its calls
    # When a Work is planned with `--title` and `--root`
    # Then the stand-in was called with the id and the roots, and the block is
    # what it returned
    raise NotImplementedError


def test_the_parent_is_the_nearest_work_above_the_place() -> None:
    """AC-6: scenario of the contract."""
    # Given Works under nesting and under flat
    # When a Work is planned by path
    # Then its parent is the Work of the nearest directory above that holds one,
    # and none under flat
    raise NotImplementedError


def test_a_bare_contract_still_works_when_no_kinds_are_declared() -> None:
    """AC-5: only `new <kind>` needs a kind."""
    # Given a config with no kinds
    # When `new` runs with a slug and no kind
    # Then the bare contract is written
    raise NotImplementedError


def test_the_parent_of_a_path_is_the_one_definition_of_the_hierarchy() -> None:
    """AC-6: `parent_of` gives the Work that `build_hierarchy` would."""
    # Given Works under nesting and under flat, and a file that is not a Work
    # When `parent_of` is asked for its parent
    # Then it is the Work of the nearest directory above that holds one, and none
    # under flat, as `build_hierarchy` gives for a Work at that path
    raise NotImplementedError
