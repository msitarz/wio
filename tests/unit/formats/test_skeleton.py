# SPDX-License-Identifier: Apache-2.0
"""Tests of the preparation of a skeleton in `wio.formats`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_comment_template_gives_a_comment_skeleton() -> None:
    """AC-1: the template's own keys, the directives and the comments are gone."""
    # Given the name `feature.leaf` and a comment template with its own keys,
    # `[contract]`, a sub-table, a comment and a directive list
    # When the skeleton is prepared, and again
    # Then it is a comment block with `template` and the contract's keys, with no
    # own key, comment or marker, the heading has lost its list, and the two
    # results are equal


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_front_matter_template_gives_a_front_matter_skeleton_with_the_marker() -> (
    None
):
    """AC-2: `+++` front matter whose first key is `wio = 1`."""
    # Given the same template written as `+++` front matter
    # When the skeleton is prepared
    # Then it is `+++` front matter with the marker first, then `template`, and
    # the same keys as the comment skeleton


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_metadata_is_template_and_the_contract_keys_and_no_id() -> None:
    """AC-3: `template` first, the keys in order, then the sub-tables."""
    # Given a template whose `[contract]` holds an `id`, a `template`, a key and
    # a sub-table, and which has its own keys
    # When the skeleton is prepared under the name `feature.leaf`
    # Then the metadata is `template`, the key and the sub-table in that order,
    # with no `id` and none of the template's own keys


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_template_without_a_contract_table_gives_only_template() -> None:
    """AC-3: no `[contract]` gives the `template` key alone."""
    # Given a template with its own keys and no `[contract]` table
    # When the skeleton is prepared
    # Then the metadata is `template` alone


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_body_keeps_everything_but_the_directive_lists() -> None:
    """AC-4: lists on real headings go, with the spaces before them."""
    # Given a body with real headings that have lists, an authoring comment and a
    # fenced block that quote a list, notes, and CRLF line endings
    # When the skeleton is prepared
    # Then only the lists of real headings are gone, the notes stay, and the
    # comment, the fenced block and the line endings are as they were


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_block_and_the_body_join_with_the_line_ending_of_the_template() -> None:
    """AC-4: the block uses the first line's ending, and an empty body is the block."""
    # Given a CRLF template, an LF template with an empty body and an LF template
    # with a body
    # When the skeleton is prepared from each
    # Then the first has CRLF in its block and body, the second is the block
    # alone ended by LF, and the third has LF throughout


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_template_that_cannot_be_prepared_is_an_error() -> None:
    """AC-5: no block, an unreadable block and a wrong list raise their errors."""
    # Given a text with no block, a block that does not close and a heading whose
    # list names an unknown directive
    # When the skeleton is prepared from each
    # Then the first says it is not a template, the second is the block reader's
    # error at line 1, and the third names the column and the line of the heading
