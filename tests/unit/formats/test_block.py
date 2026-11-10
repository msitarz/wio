# SPDX-License-Identifier: Apache-2.0
"""Tests of the reader of the metadata block in `wio.formats`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_both_forms_give_their_form_version_data_and_body() -> None:
    """AC-1: each form is split into its parts and the body is kept as it was."""
    # Given a comment block, one with text after `-->`, one with CRLF and a
    # `+++` block
    # When each is read
    # Then the form, the version, the data, the body and its start line are
    # those of the contract, and the body is the text from that line on


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_marker_is_optional_in_a_comment_and_checked_everywhere() -> None:
    """AC-2: an absent marker is version 1, and any marker but 1 is refused."""
    # Given comment blocks with no marker and with `wio = 1`, and blocks of both
    # forms whose marker is 2, true, "1" or 1.0
    # When each is read
    # Then the first give version 1 and the rest raise an error that names the
    # marker


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_text_that_is_not_marked_gives_nothing() -> None:
    """AC-3: a text without wio's block gives `None` and raises nothing."""
    # Given texts with no block, a late comment, `<!-- wiox` and front matter
    # that is not wio's
    # When each is read
    # Then each gives nothing


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_block_that_cannot_be_read_is_an_error_with_its_line() -> None:
    """AC-4: an unclosed or invalid block raises an error at its line."""
    # Given blocks that never close, that hold invalid TOML, or that close at
    # the first `-->`
    # When each is read
    # Then each raises an error that names the line of the text


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_line_endings_and_the_byte_order_mark_do_not_change_the_result() -> None:
    """AC-5: LF, CRLF and a leading U+FEFF read alike."""
    # Given one block of each form written three ways
    # When each is read
    # Then the form, the version, the data and the body start line are equal
