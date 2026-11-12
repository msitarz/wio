# SPDX-License-Identifier: Apache-2.0
"""Test stubs of setting keys in the metadata block of a contract.

Each stub is a scenario of the Work's acceptance criteria. The implementation
stage replaces its body with the scenario.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="architecture stub: the implementation stage fills it"
)


def test_keys_and_tables_are_set_in_both_block_forms() -> None:
    """AC-8: the requested values are set in either form."""
    # Given a comment block with roots and a table, and front matter with a marker
    # When id, roots, dependencies and a table are set
    # Then the requested values and the untouched table and marker are present
    raise NotImplementedError


def test_existing_keys_and_tables_are_replaced() -> None:
    """AC-8: a replacement is not merged with the old value."""
    # Given a block with an id and an actions table
    # When both are set to new values
    # Then the id and the table have the new values, without the old table keys
    raise NotImplementedError


def test_replacing_a_table_retains_untouched_comments() -> None:
    """AC-8: table replacement keeps comments outside its replaced values."""
    # Given a table with comments beside its header and entries, and trailing
    # comments before another table
    # When the table is replaced with different entries
    # Then untouched comments remain, the old values are gone and the new ones
    # and the other table are present
    raise NotImplementedError


def test_a_block_with_no_keys_gets_its_keys() -> None:
    """AC-8: an empty block can receive keys."""
    # Given an empty comment block
    # When an id and roots are set
    # Then the block holds both values
    raise NotImplementedError


def test_the_line_endings_and_the_byte_order_mark_are_kept() -> None:
    """AC-8: CRLF and the byte-order mark survive editing."""
    # Given a contract written with CRLF and one with a byte-order mark
    # When keys and a table are set
    # Then every line ending is CRLF, the mark is there, and the body is as it was
    raise NotImplementedError


def test_a_block_that_mixes_line_endings_keeps_them() -> None:
    """AC-8: existing line endings are preserved."""
    # Given a block whose lines end with LF and CRLF, and a body with CRLF
    # When keys are set
    # Then existing line endings and the body are as they were, and the added line
    # uses the opening delimiter's ending
    raise NotImplementedError


def test_untouched_values_comments_body_and_delimiters_are_kept() -> None:
    """AC-8: editing keeps the untouched content."""
    # Given a block with comments, dotted keys and a multiline string containing
    # empty and comment-like lines, and a body that looks like metadata
    # When a key is added
    # Then the untouched values and comments, body and delimiters are retained
    raise NotImplementedError


def test_a_mapping_in_the_plain_keys_is_written_as_an_inline_table() -> None:
    """AC-8: an inline table counts as a plain key."""
    # Given a block with a plain key
    # When a plain key whose value is a mapping is set
    # Then its value is written as an inline table
    raise NotImplementedError


def test_a_mapping_inside_an_array_is_written() -> None:
    """AC-8: an array can contain inline tables."""
    # Given a block with a plain key
    # When a key whose value is a list of mappings is set
    # Then the key is added with an array containing an inline table
    raise NotImplementedError


def test_a_table_named_like_a_plain_key_is_refused() -> None:
    """AC-8: a name cannot be a plain key and a table."""
    # Given a block with the inline table `actions = { a = 1 }` and one with `[x]`
    # When the table `actions` is set on the first, and the plain key `x` on the second
    # Then `ValueError` is raised for each
    raise NotImplementedError


def test_a_text_with_no_block_is_refused() -> None:
    """AC-8: the block reader reports an absent block."""
    # Given a text with no metadata block
    # When keys are set
    # Then the error of the block reader is raised
    raise NotImplementedError
