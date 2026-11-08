# SPDX-License-Identifier: Apache-2.0
"""Tests of finding what a key path names in a config."""

import pytest


def test_a_key_path_names_a_setting_or_a_table() -> None:
    """A leaf is a single setting and anything with keys is a table."""
    # Given a config with two stages
    # When a key path is resolved
    # Then it names a single setting or a table, in canonical form
    pytest.skip("stub: the implementation stage writes this test")


def test_a_table_covers_the_settings_below_it_and_not_a_sibling() -> None:
    """The prefix match respects the dot."""
    # Given the target `stages.define`
    # When it is asked about a setting below it and a similarly named one
    # Then only the first is covered
    pytest.skip("stub: the implementation stage writes this test")


def test_a_single_setting_covers_only_itself() -> None:
    """A single target does not take the keys that start with its path."""
    # Given the target of one setting
    # When it is asked about itself and about a longer path
    # Then it covers only itself
    pytest.skip("stub: the implementation stage writes this test")


def test_the_whole_config_covers_every_setting() -> None:
    """The empty target is the root."""
    # Given the target of the whole config
    # When it is asked about any setting
    # Then it covers it
    pytest.skip("stub: the implementation stage writes this test")


def test_an_unknown_top_level_key_names_the_closest_and_the_valid_keys() -> None:
    """`stage` is a typo of `stages`."""
    # Given a config
    # When a misspelled top-level key is resolved
    # Then the message names the closest match and the valid top-level keys
    pytest.skip("stub: the implementation stage writes this test")


def test_an_unknown_entry_names_the_closest_path_and_the_entries() -> None:
    """`definer` is a typo of the stage `define`."""
    # Given a config with the stage `define`
    # When a misspelled stage is resolved
    # Then the message names `stages.define` and the stages
    pytest.skip("stub: the implementation stage writes this test")


def test_an_unknown_key_in_an_empty_table_says_it_has_no_entries() -> None:
    """There is nothing to suggest under `roots` when no root is declared."""
    # Given a config without roots
    # When an entry of roots is resolved
    # Then the message says the table has no entries
    pytest.skip("stub: the implementation stage writes this test")


def test_an_optional_setting_that_is_not_set_is_refused() -> None:
    """`judge` has no value."""
    # Given a stage without a judge
    # When the judge is resolved
    # Then the message says it is not set
    pytest.skip("stub: the implementation stage writes this test")


def test_an_item_of_a_list_is_refused_and_the_list_is_named() -> None:
    """A list is shown whole."""
    # Given a stage with a `rules_include` list
    # When an item of it is resolved
    # Then the message says a list is shown whole, as the list's own key path
    pytest.skip("stub: the implementation stage writes this test")


def test_an_index_after_a_key_that_holds_no_list_is_refused() -> None:
    """`hierarchy` is a string."""
    # Given a config
    # When an index follows a string setting
    # Then the message says it is not a list
    pytest.skip("stub: the implementation stage writes this test")


def test_a_key_below_a_setting_is_refused() -> None:
    """A setting has no keys."""
    # Given a config
    # When a key is asked below a setting
    # Then the message says the setting has no key
    pytest.skip("stub: the implementation stage writes this test")


def test_a_malformed_key_path_explains_the_syntax() -> None:
    """The message points at the place and shows a good key path."""
    # Given a text that is not a key path
    # When it is resolved
    # Then the message says it is not a key path and gives an example
    pytest.skip("stub: the implementation stage writes this test")
