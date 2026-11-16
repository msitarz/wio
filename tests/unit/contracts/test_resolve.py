# SPDX-License-Identifier: Apache-2.0
"""Test stubs of the resolved view of a Work.

Each stub is a scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario and its fixture.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


def test_the_view_holds_the_work_and_what_its_parent_passes_on() -> None:
    """AC-1: a child of a parent."""
    # Given a parent that marks Glossary and Constraints inherit, and a child
    # When the view of the child is rendered
    # Then it is exactly the text of AC-1, ending in one line ending
    raise NotImplementedError


def test_the_nearest_ancestor_that_passes_comes_first_and_the_others_are_skipped() -> (
    None
):
    """AC-2: three levels."""
    # Given a grandparent that marks Constraints, a parent that marks nothing, a
    # child and a Work with no parent
    # When the views of the child and of the lone Work are rendered
    # Then the child has one `## Inherited from:` section, for the grandparent,
    # and the lone Work has its own contract only
    raise NotImplementedError


def test_two_ancestors_that_pass_come_nearest_first() -> None:
    """AC-2: two ancestors that pass."""
    # Given the same tree with the parent marking Constraints too
    # When the view of the child is rendered
    # Then the section for the parent comes before the one for the grandparent
    raise NotImplementedError


def test_under_flat_every_view_is_the_own_contract_only() -> None:
    """AC-2: under flat."""
    # Given `hierarchy = "flat"` and the same tree
    # When the views of g, p and c are rendered
    # Then each is its own contract only
    raise NotImplementedError


def test_a_template_marks_sections_matched_by_text_and_a_stray_mark_is_ignored() -> (
    None
):
    """AC-3: a template and a text match."""
    # Given an ancestor whose `## constraints` differs in case and has a
    # trailing space, and a stray inherit on its Purpose
    # When the view of its child is rendered
    # Then it holds `### constraints` and not the Purpose
    raise NotImplementedError


def test_without_a_template_the_ancestors_own_headings_mark_and_a_repeat_passes() -> (
    None
):
    """AC-3: no template and a repeated section."""
    # Given an ancestor with no template and `## Rules` marked inherit twice
    # When the view of its child is rendered
    # Then it holds `### Rules` twice, in order, without the comment, no Notes
    raise NotImplementedError


def test_an_ancestor_whose_template_cannot_be_used_passes_nothing_and_stops_nothing() -> (  # noqa: E501
    None
):
    """AC-4: three ancestors."""
    # Given children of a missing, a rejected and an unreadable template, under a
    # grandparent with an inheritable Constraints
    # When the three views are rendered
    # Then each holds the child's contract and one section for the grandparent
    raise NotImplementedError


def test_the_metadata_block_and_directive_lists_are_cleaned_and_the_text_repeats() -> (
    None
):
    """AC-5: cleaning."""
    # Given a CRLF child with front matter and a parent with a comment-only
    # Glossary and a stray inherit on Purpose
    # When the view of the child is rendered twice
    # Then both are the text of AC-5, with LF endings only
    raise NotImplementedError


def test_a_level_six_heading_stays_and_a_bad_directive_list_is_left_as_written() -> (
    None
):
    """AC-5: a deep heading and a bad list."""
    # Given an ancestor with a level-6 heading and `## Rules` with a bad list
    # When the view of a child is rendered
    # Then the level-6 heading stays at 6 and the bad list stays in its heading
    raise NotImplementedError


def test_files_that_cannot_be_read_pass_nothing_and_raise_nothing() -> None:
    """AC-5: files that cannot be read."""
    # Given a file system that raises OSError on the resolver's own read of one
    # parent's template and of another parent's file
    # When the views of the two children are rendered
    # Then each holds the child's contract and one section for the grandparent
    raise NotImplementedError


def test_a_section_runs_to_the_next_heading_of_level_one_or_two() -> None:
    """AC-6: the extent of a section."""
    # Given a parent whose Constraints holds only a level-3 heading and a `# Next`
    # that ends it, then Notes
    # When the view of a child with an empty own contract is rendered
    # Then it is exactly the text of AC-6
    raise NotImplementedError


def test_a_title_with_a_directive_list_is_named_without_it() -> None:
    """AC-6: an ancestor whose title carries a directive list."""
    # Given a parent whose title is `# Parent <!-- wio: required -->`
    # When the view of a child with an empty own contract is rendered
    # Then it begins with `## Inherited from: Parent (p5n2hv)`
    raise NotImplementedError


def test_an_ancestor_without_a_level_one_heading_is_named_by_its_first_heading() -> (
    None
):
    """AC-6: an ancestor named by its first heading."""
    # Given a parent whose body starts with `## Purpose`
    # When the view of a child with an empty own contract is rendered
    # Then it begins with `## Inherited from: Purpose (p5n2hv)`
    raise NotImplementedError
