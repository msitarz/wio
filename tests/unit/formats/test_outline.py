# SPDX-License-Identifier: Apache-2.0
"""Tests of the outline of a Markdown body in `wio.formats`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_headings_come_with_their_level_text_raw_line_and_file_line() -> None:
    """AC-1: each real heading is returned in order, with its four fields."""
    # Given a body with headings of level 1, 2 and 6, starting on line 10
    # When the outline reads it
    # Then three headings are returned, with their level, text, raw line and
    # line in the file


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_body_without_a_heading_has_no_headings() -> None:
    """AC-1: two paragraphs give nothing."""
    # Given a body of two paragraphs
    # When the outline reads it
    # Then it returns no headings


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_text_leaves_out_the_marks_and_spaces_around_it() -> None:
    """AC-2: no leading or closing `#` marks, no spaces, and the raw line is whole."""
    # Given closed headings, one with extra spaces and two trailing spaces
    # When the outline reads them
    # Then the texts are bare and each raw line is the whole line, spaces kept


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_line_that_only_looks_like_a_heading_is_not_one() -> None:
    """AC-3: code, comments, quotes, lists and setext lines hold no heading."""
    # Given seven bodies, each with a look-alike and then a real heading
    # When the outline reads each
    # Then each returns the real heading only, on its own line


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_line_endings_do_not_change_the_headings() -> None:
    """AC-4: CRLF and LF give equal results, and no raw line ends in a CR."""
    # Given one body written with LF and with CRLF
    # When the outline reads both
    # Then the results are equal and no raw line ends in a carriage return
