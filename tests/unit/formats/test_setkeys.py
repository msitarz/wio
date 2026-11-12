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
    # Given a block with an inline table, one with a table directly after its key,
    # one with a comment directly above its table, and one with a table and no
    # plain keys
    # When a plain key is added to each, and a table to the first
    # Then the key follows the inline table or goes first, the existing tables gain
    # no empty line, and only the added table is preceded by one
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


def test_a_table_that_is_there_is_replaced_in_place_by_the_one_given() -> None:
    """AC-8: an existing table keeps its position and is not merged."""
    # Given a block with a table `[actions]` that holds `deliver` and `ratify`
    # When the table `[actions]` is set with `deliver` and `amend`
    # Then the table is where it was and holds `deliver` and `amend` only
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


def test_a_new_plain_key_goes_right_after_the_last_plain_key() -> None:
    """AC-8: the key goes before the comment lines that follow the last plain key."""
    # Given a block with `template`, a comment line, an empty line and a table
    # When a plain key is added
    # Then it follows `template` directly, before the comment line, and the empty
    # line and the table are as they were
    raise NotImplementedError


def test_an_added_table_adds_an_empty_line_only_when_there_is_none() -> None:
    """AC-8: one empty line separates an added table from what precedes it."""
    # Given a block that ends with no empty line, one that ends with one, one that
    # ends with two, and an empty block
    # When a table is added to each
    # Then one empty line is added to the first, none to the others, and the
    # empty block gets the table with no empty line before it
    raise NotImplementedError


def test_a_table_named_like_a_plain_key_is_refused() -> None:
    """AC-8: a name cannot be a plain key and a table."""
    # Given a block with the inline table `actions = { a = 1 }` and one with the
    # table `[x]`
    # When the table `actions` is set on the first, and the plain key `x` on the
    # second
    # Then `ValueError` is raised for each
    raise NotImplementedError


def test_a_block_with_no_final_line_ending_is_given_one() -> None:
    """AC-8: the last line of the block ends with the line ending."""
    # Given a front matter block whose last table line has no line ending before
    # the closing delimiter, and the same with a table to add
    # When a table is added
    # Then the table follows after an empty line and every line ends with the
    # line ending of the block
    raise NotImplementedError


def test_a_mapping_inside_an_array_is_written() -> None:
    """AC-8: an array can contain inline tables."""
    # Given a block with a plain key
    # When a key whose value is a list of mappings is set
    # Then the key is added with an array containing an inline table
    raise NotImplementedError


def test_multiline_values_and_dotted_keys_are_preserved() -> None:
    """AC-8: adding a key does not alter a multiline value or dotted key."""
    # Given a block with a dotted key and a multiline string containing empty and
    # comment-like lines
    # When a plain key is added
    # Then it follows the complete last plain key and the existing text is unchanged
    raise NotImplementedError


def test_an_empty_line_before_a_plain_key_stays_where_it_is() -> None:
    """AC-8: a key is added after the last plain key and moves nothing."""
    # Given blocks with an empty line before the last plain key, a comment line
    # and an empty line before it, and an empty line at the start of the block
    # When a plain key is added to each
    # Then the key follows the last plain key, and every other line, empty or not,
    # is where it was
    raise NotImplementedError
