# SPDX-License-Identifier: Apache-2.0
"""Tests of the list of settings and of the lines that show them."""

import pytest


def test_settings_are_sorted_by_key_path_and_carry_their_source() -> None:
    """Each set value and each default is listed once, in key-path order."""
    # Given a config that sets some stage keys and leaves the rest to defaults
    # When its settings are listed
    # Then they are sorted and each one knows whether the file or a default set it
    pytest.skip("stub: the implementation stage writes this test")


def test_a_key_that_needs_quotes_is_quoted_in_its_path() -> None:
    """A stage named with a dot is listed under a TOML-quoted key."""
    # Given a config with a stage named `a.b`
    # When its settings are listed
    # Then the key path quotes the name as TOML does
    pytest.skip("stub: the implementation stage writes this test")


def test_an_optional_setting_that_is_not_set_is_not_listed() -> None:
    """A setting with no value has no line."""
    # Given a stage without a judge and a bundle without a size threshold
    # When its settings are listed
    # Then neither is in the list
    pytest.skip("stub: the implementation stage writes this test")


def test_a_multi_line_string_shows_its_first_line_and_an_ellipsis() -> None:
    """The short line keeps the first line of the goal and marks the cut."""
    # Given a goal of three lines
    # When its short line is written
    # Then the first line is shown, then an ellipsis and the closing quote
    pytest.skip("stub: the implementation stage writes this test")


def test_a_long_string_is_cut_so_that_the_line_is_80_columns() -> None:
    """The label stays whole and the value gives way."""
    # Given a description of ninety characters
    # When its short line is written
    # Then the line is at most 80 columns and ends with the cut mark and label
    pytest.skip("stub: the implementation stage writes this test")


def test_a_list_loses_items_from_its_end_to_fit() -> None:
    """An array that does not fit keeps its leading items and an ellipsis."""
    # Given a list setting with a long key path
    # When its short line is written
    # Then it is at most 80 columns and shows the leading items then the mark
    pytest.skip("stub: the implementation stage writes this test")


def test_a_value_that_does_not_fit_at_all_is_an_ellipsis() -> None:
    """When the key path and the label leave no room, the value is `…`."""
    # Given a setting whose key path and label reach 80 columns
    # When its short line is written
    # Then the value is an ellipsis and the key path and label are whole
    pytest.skip("stub: the implementation stage writes this test")


def test_an_array_that_cannot_show_one_item_is_an_ellipsis() -> None:
    """With room for no item the array gives way to `…`."""
    # Given a list and a key path that leave room for two columns
    # When its short line is written
    # Then the value is an ellipsis
    pytest.skip("stub: the implementation stage writes this test")


def test_the_full_line_shows_the_whole_value() -> None:
    """Nothing is shortened, and a newline is written as an escape."""
    # Given the three-line goal
    # When its full line is written
    # Then every line of the goal is in it on one line
    pytest.skip("stub: the implementation stage writes this test")


def test_values_are_written_in_toml_syntax() -> None:
    """Strings are quoted and lists are arrays."""
    # Given a string, a boolean, an integer and a list of strings
    # When each is written as a setting's value
    # Then it appears as the config file would hold it
    pytest.skip("stub: the implementation stage writes this test")


def test_a_control_character_is_escaped_in_a_quoted_string() -> None:
    """A string holds no raw control character once quoted."""
    # Given a string with a tab, a backslash and a bell
    # When it is quoted
    # Then each is escaped as TOML escapes it
    pytest.skip("stub: the implementation stage writes this test")
