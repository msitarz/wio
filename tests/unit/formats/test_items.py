# SPDX-License-Identifier: Apache-2.0
"""Tests of the items of a section in `wio.formats`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_subheadings_of_a_section_are_its_items_and_win_over_a_list() -> None:
    """AC-1: the headings one level below the section, with their text and file line."""
    # Given a body starting at line 10 with an intro bullet, two `###` criteria
    # around a `####` heading, and a next section with a `###` heading
    # When the items of the section are found
    # Then the two criteria are returned in order on lines 14 and 18, and
    # the bullet, the `####` heading and the next section's heading are not items


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_list_items_of_a_section_are_its_items_when_it_has_no_subheading() -> None:
    """AC-1: top-level list items, ordered or not, in a body with CRLF endings."""
    # Given a CRLF body with a bullet that has a nested one, a numbered item, a
    # quoted list, a comment with a list and a fenced block with a list
    # When the items of the section are found
    # Then they are `one` on line 3 and `two` on line 6, and nothing else


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_list_after_a_deeper_heading_is_not_an_item() -> None:
    """AC-1: only the list items before the first deeper heading count."""
    # Given a section with a bullet, a `####` heading and a bullet under it
    # When its items are found
    # Then the only item is the first bullet


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_list_item_that_opens_with_a_code_block_has_empty_text_and_no_id() -> None:
    """AC-1: no paragraph first gives the empty text and one error."""
    # Given a section with pattern `N-\d+` and a list item that opens with a
    # fenced block
    # When its items are found and judged
    # Then the item has the empty text and no id, and there is one error


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_section_with_only_prose_or_a_comment_has_no_items() -> None:
    """AC-1: prose and an authoring comment hold no item."""
    # Given a section of prose and a section of one authoring comment
    # When the items of each are found
    # Then both have none


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_id_is_the_pattern_match_after_leading_markup() -> None:
    """AC-2: the match at the start, after `*`, `_`, backticks and spaces."""
    # Given pattern `AC-\d+` and items with markup, a mid-text id and a prefix
    # When the items are found
    # Then the ids are `AC-1`, `AC-2`, none, `AC-12` and none


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_list_item_has_its_id_after_its_marker() -> None:
    """AC-2: bullets and numbered items give their ids."""
    # Given pattern `A-\d+` and the list items `- **A-1**: first` and `2. A-2 second`
    # When the items are found
    # Then the ids are `A-1` and `A-2`


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_an_empty_match_is_no_id() -> None:
    r"""AC-2: the pattern `\d*` gives no id for `Plain` and `7` for `7 seven`."""
    # Given pattern `\d*` and the items `Plain` and `7 seven`
    # When the items are found
    # Then the first has no id and the second has the id `7`


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_section_without_a_pattern_gives_no_ids() -> None:
    """AC-2: no pattern, no id."""
    # Given a section with items and no pattern
    # When the items are found
    # Then none has an id


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_too_few_items_is_an_error_at_the_heading() -> None:
    """AC-3: `items>=3` on two items, and `items>=1` on a comment only."""
    # Given `items>=3` on a section with two items and `items>=1` on a section
    # of a comment
    # When the items are judged
    # Then each is an error at its heading that names `items` and says how many
    # items it holds and needs


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_an_item_without_an_id_is_an_error_at_the_item() -> None:
    """AC-3: one error at the item `Replaces AC-3`, none for the others."""
    # Given pattern `AC-\d+` on a section whose second item is `Replaces AC-3`
    # When the items are judged
    # Then one error at that line names `pattern`, and none is for the others


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_unmarked_items_are_free() -> None:
    """AC-3: neither `items` nor `pattern` gives no diagnostic."""
    # Given a section with items and no directive
    # When the items are judged
    # Then there is no diagnostic


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_repeated_id_is_one_error_at_the_first_occurrence() -> None:
    """AC-4: in one section or two, naming the lines of the others."""
    # Given `AC-1` twice in one section and once in the next, on lines 12, 14 and 18
    # When the items are judged
    # Then one error at line 12 names `AC-1` and the lines 14 and 18


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_an_id_with_whitespace_or_a_comma_is_an_error_at_its_item() -> None:
    r"""AC-4: patterns `AC \d` and `A,\d` give bad ids."""
    # Given the two patterns and the items `AC 1` and `A,1`
    # When the items are judged
    # Then each is an error at its line that says the id holds whitespace or a comma
