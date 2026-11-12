# SPDX-License-Identifier: Apache-2.0
"""Test stubs of setting keys in the metadata block of a contract.

Each stub is a scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


def test_the_id_goes_first_and_the_other_keys_are_set_by_the_rules() -> None:
    """AC-8: scenario of the contract."""
    # Given a contract with a comment block holding `template`, `roots = []`, an
    # empty line and a table `[x]`, and one with `+++` front matter
    # When the id, the roots and the dependencies are set, and then the table
    # `[actions]`
    # Then the id is first, `roots` is replaced in place, `depends_on` follows
    # the last plain key, `[x]` is as it was and `[actions]` comes last after an
    # empty line, and the front matter has `wio = 1` then the id
    raise NotImplementedError


def test_a_key_that_is_there_is_replaced_in_place() -> None:
    """AC-8: scenario of the contract."""
    # Given a block whose `id` and `template` are in the middle of other keys
    # When they are set again
    # Then they keep their positions and the rest of the text
    raise NotImplementedError


def test_an_inline_table_is_a_plain_key_and_only_an_added_table_has_an_empty_line() -> (
    None
):
    """AC-8: scenario of the contract."""
    # Given a block with an inline table and one with a table and no plain keys
    # When a plain key and a table are added
    # Then the key follows the inline table, the table follows the plain keys
    # when there is none, and only the table is preceded by an empty line
    raise NotImplementedError


def test_a_block_with_no_keys_gets_its_keys() -> None:
    """AC-8: scenario of the contract."""
    # Given `<!-- wio` and `-->` with nothing between them
    # When an id and roots are set
    # Then the block holds them, the id first
    raise NotImplementedError


def test_the_line_ending_and_the_byte_order_mark_are_kept() -> None:
    """AC-8: scenario of the contract."""
    # Given a contract written with CRLF and one with a byte-order mark
    # When keys and a table are set
    # Then every line ending is CRLF, the mark is there, and the body is as it was
    raise NotImplementedError


def test_nothing_but_the_block_changes() -> None:
    """AC-8: scenario of the contract."""
    # Given a contract with comments in its block, a body with lines that look
    # like keys and a closing delimiter
    # When keys are set
    # Then the comments, the body and the delimiters are as they were
    raise NotImplementedError


def test_a_text_with_no_block_is_refused() -> None:
    """AC-8: scenario of the contract."""
    # Given a text with no metadata block
    # When keys are set
    # Then the error of the block reader is raised
    raise NotImplementedError


def test_a_table_that_is_there_has_its_keys_set_in_place_or_added() -> None:
    """AC-8: an existing table is merged and keeps its position."""
    # Given a block with a table `[actions]` that holds `deliver`
    # When the table `[actions]` is set with a new `deliver` and an `amend`
    # Then `deliver` is replaced in place and `amend` follows it, and the table
    # stays where it was
    raise NotImplementedError


def test_a_mapping_in_the_plain_keys_is_written_as_an_inline_table() -> None:
    """AC-8: an inline table counts as a plain key."""
    # Given a block with a plain key
    # When a plain key whose value is a mapping is set
    # Then it is written as an inline table after the last plain key
    raise NotImplementedError


def test_a_block_that_mixes_line_endings_is_written_with_the_first_one() -> None:
    """AC-8: the block is the one place that is rewritten."""
    # Given a block whose lines end with LF and CRLF, and a body with CRLF
    # When keys are set
    # Then every line ending of the block is that of its first line, and the body
    # is as it was
    raise NotImplementedError


def test_a_new_plain_key_follows_the_comment_lines_after_the_last_plain_key() -> None:
    """AC-8: the key goes after the comments that follow the last plain key."""
    # Given a block with `template`, a comment line, an empty line and a table
    # When a plain key is added
    # Then it follows the comment line and comes before the empty line and the table
    raise NotImplementedError


def test_the_empty_lines_a_block_already_has_are_kept_and_only_one_is_added() -> None:
    """AC-8: an added table adds one empty line, and no key adds any."""
    # Given a block that ends with two empty lines after its last plain key
    # When a table is added
    # Then the two empty lines are kept and no empty line is added before the table
    raise NotImplementedError
