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
    # Then the output is one array with an object for each entry in the table's
    # order, whose four fields equal the entry's


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
