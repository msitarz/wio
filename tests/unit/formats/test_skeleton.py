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
    # Given, one case at a time and parametrized: a heading with a list, a
    # multi-line authoring comment that quotes a list, a fenced block that holds
    # the same heading, a heading with a note, a heading with a note and then a
    # list, and the same body with CRLF line endings
    # When the skeleton is prepared
    # Then only the lists of real headings are gone, and the comment, the fenced
    # block, the note and the line endings are as they were


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_block_and_the_body_join_with_the_line_ending_of_the_template() -> None:
    """AC-4: the block uses the first line's ending, and an empty body is the block."""
    # Given, parametrized: a CRLF template, an LF template whose body is empty
    # and an LF template with a body, and a template that starts with a
    # byte-order mark
    # When the skeleton is prepared from each
    # Then the first has CRLF in its block and body, the second is the block
    # alone ended by LF, the third has LF throughout, and the last keeps its mark
    # at the start


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_text_with_no_block_is_not_a_template() -> None:
    """AC-5: a text without a metadata block is refused as not a template."""
    # Given a text that has no metadata block
    # When the skeleton is prepared
    # Then it raises an error that says it is not a template


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_block_that_does_not_close_raises_the_error_of_the_block_reader() -> None:
    """AC-5: the block reader's error is not changed, and names line 1."""
    # Given a comment block that does not close
    # When the skeleton is prepared
    # Then it raises the block reader's error naming line 1


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_wrong_directive_list_names_the_column_and_the_line_of_its_heading() -> None:
    """AC-5: the heading's line comes from the outline, so it is not line 1."""
    # Given a template whose heading on a later line has the list
    # `<!-- wio: mandatory -->`
    # When the skeleton is prepared
    # Then it raises the directive parser's error with the column of the problem
    # and the line of the heading in the text
