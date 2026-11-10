# SPDX-License-Identifier: Apache-2.0
"""Tests of the directive grammar in `wio.formats`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_directive_list_is_read_into_typed_directives_in_order() -> None:
    """AC-1: a heading gives its text, level and directives as written."""
    # Given a level-2 heading with `required`, `items>=1` and a pattern
    # When the parser reads it
    # Then the text, the level 2 and the directives come in the order written


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_spaces_around_the_parts_of_a_list_are_allowed() -> None:
    """AC-1: spaces around `wio:`, the commas, `>=` and `=` change nothing."""
    # Given headings with spaces and none around the opener, commas and operators
    # When the parser reads each
    # Then each gives the directives that the contract names


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_pattern_is_plain_or_between_quotes() -> None:
    """AC-2: a plain pattern runs to the next comma, a quoted one to its quote."""
    # Given headings with plain, quoted and spaced patterns
    # When the parser reads each
    # Then the patterns are those of the contract, trimmed, with inner spaces kept


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_literal_quote_and_angle_bracket_are_written_as_hex_escapes() -> None:
    """AC-2: `\\x22` and `\\x3e` stay as written, for `re` to read."""
    # Given a heading whose pattern holds `\x22` and `\x3e`
    # When the parser reads it
    # Then the pattern is kept as written


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_line_with_no_directive_list_gives_no_directives_and_no_error() -> None:
    """AC-3: notes and near-misses are text, and a non-heading gives `None`."""
    # Given headings without a list, with notes and near-miss openers, a note
    # before a list, and a line that is not a heading
    # When the parser reads each
    # Then the text keeps its comments, no directives are given and none raises,
    # and the non-heading gives `None`


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_list_with_a_wrong_name_or_shape_is_an_error_with_its_column() -> None:
    """AC-4: each wrong list raises an error that names its column."""
    # Given headings with an unknown name or one in the wrong case, a repeated
    # name, an empty list, an unclosed list, text after a list and two lists
    # When the parser reads each
    # Then each raises an error with its message and the column of the contract


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_directive_with_a_wrong_value_is_an_error_with_its_column() -> None:
    """AC-5: each wrong value raises an error that names its column."""
    # Given headings whose `items`, `required`, `inherit` or `pattern` has a
    # wrong value
    # When the parser reads each
    # Then each raises an error with the column of the contract, and the pattern
    # that does not compile carries the message of `re`


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_level_is_returned_and_not_restricted() -> None:
    """AC-6: a list on a level-3 heading is read and its level is returned."""
    # Given a level-3 heading with a list
    # When the parser reads it
    # Then the level is 3 and the directive is read


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_table_lists_every_directive_in_order() -> None:
    """AC-7: the entries are in order, each with a syntax, a meaning, examples."""
    # Given the table of directives
    # When its entries are read in order
    # Then the names are `required`, `items`, `pattern` and `inherit`, `pattern`
    # has two examples and the others one


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_every_example_of_the_table_parses_into_its_directive() -> None:
    """AC-7: the parser reads each example into the directive it documents."""
    # Given the table of directives
    # When the parser reads the example of each entry
    # Then it gives the directives that the entry documents and raises no error
