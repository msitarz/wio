# SPDX-License-Identifier: Apache-2.0
"""Tests of the rendering of `wio templates directives` in `wio.templates`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_human_form_prints_each_entry_of_the_table_as_it_is() -> None:
    """AC-1: a block for each entry, in order, with the table's own fields."""
    # Given a table of entries, one with a meaning of two lines and one with two
    # examples
    # When it is rendered for a person
    # Then each entry is a block of the name, `Syntax:`, the meaning indented by
    # two spaces on each line, and an `Example:` line for each example, with one
    # empty line between blocks and none after the last


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_json_form_is_one_array_of_the_entries_in_order() -> None:
    """AC-2: objects with `name`, `syntax`, `meaning` and `examples`."""
    # Given a table of entries
    # When it is rendered as JSON
    # Then the output is one compact array ending in a line ending, with an
    # object for each entry in the table's order, whose four fields equal the
    # entry's in the order name, syntax, meaning and examples


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_real_table_is_printed_whole_and_in_its_order() -> None:
    """AC-1: the entries of `DIRECTIVES` come out unsorted and unfiltered."""
    # Given the table of the directive parser
    # When it is rendered in both forms
    # Then every entry is there once, in the order `required`, `items`, `pattern`,
    # `inherit`, and nothing else is added


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_same_table_always_gives_the_same_text() -> None:
    """AC-7: both forms are the same on every call."""
    # Given the table of the directive parser
    # When each form is rendered twice
    # Then the two results of each form are identical


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_an_empty_table_gives_nothing_or_an_empty_array() -> None:
    """AC-1 and AC-2: no entry is an empty text, or `[]` for JSON."""
    # Given an empty table
    # When it is rendered for a person and as JSON
    # Then the first is empty and the second is an empty array with its ending


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_an_entry_with_no_example_has_no_example_line_and_an_empty_array() -> None:
    """AC-1 and AC-2: the examples are printed as they are, even when none."""
    # Given an entry with no example
    # When it is rendered in both forms
    # Then its block has no `Example:` line and its object has an empty array
