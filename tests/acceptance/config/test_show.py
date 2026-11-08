# SPDX-License-Identifier: Apache-2.0
"""Scenarios of the Work that shows the settings: `wio config list` and `show`."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

# Git runs in every scenario, so none of them is fast.
pytestmark = [
    pytest.mark.slow,
    pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI),
]


def test_bare_config_shows_the_help(wio: Wio) -> None:
    """AC-1: bare `wio config` names its subcommands and exits 0."""
    # Given a repository with a valid config
    # When `wio config` runs
    # Then the output names list and show and the exit code is 0
    del wio
    pytest.skip("stub: the implementation stage writes this test")


def test_list_shortens_the_lines_and_labels_the_sources(wio: Wio) -> None:
    """AC-2: each setting is a line of at most 80 columns, in key-path order."""
    # Given a config with a three-line goal and a ninety-character description
    # When the settings are listed
    # Then the goal shows its first line, every line fits and the order is sorted
    del wio
    pytest.skip("stub: the implementation stage writes this test")


def test_list_keeps_a_long_key_whole(wio: Wio) -> None:
    """AC-2: a key path and a label that reach 80 columns leave `…` for the value."""
    # Given a stage whose name makes the key path and the label reach 80 columns
    # When the settings are listed
    # Then its goal shows as an ellipsis, with the key path and label whole
    del wio
    pytest.skip("stub: the implementation stage writes this test")


def test_list_json_keeps_every_value(wio: Wio) -> None:
    """AC-2: the JSON object maps each key path to its value and source."""
    # Given the same config
    # When the settings are listed as JSON
    # Then values are whole and the keys are sorted
    del wio
    pytest.skip("stub: the implementation stage writes this test")


def test_show_a_setting_adds_its_description(wio: Wio) -> None:
    """AC-3: a setting prints its line, the description below and JSON."""
    # Given a config that sets the hierarchy to nesting
    # When the setting is shown as text and as JSON
    # Then the text has the line and the description, the JSON one entry
    del wio
    pytest.skip("stub: the implementation stage writes this test")


def test_show_a_table_and_the_whole_config(wio: Wio) -> None:
    """AC-3: a table and the whole config print their settings in full."""
    # Given a config with two stages, one with a three-line goal
    # When the stages and the whole config are shown, and the stages as JSON
    # Then the goal is whole, no description is printed and JSON is restricted
    del wio
    pytest.skip("stub: the implementation stage writes this test")


def test_show_unset_empty_and_inside_a_list(wio: Wio) -> None:
    """AC-3: an unset setting and a list item exit 2, an empty table exits 0."""
    # Given a stage without a judge, no roots and a rules_include list
    # When each is shown
    # Then they exit 2, print nothing (or {}) and exit 0, and exit 2
    del wio
    pytest.skip("stub: the implementation stage writes this test")


def test_show_an_unknown_key_path_suggests_the_closest(wio: Wio) -> None:
    """AC-3: a typo names the closest match and the valid keys."""
    # Given a config with a stage `define`
    # When two misspelled key paths are shown
    # Then both exit 2, the first names `stages` and the second `stages.define`
    del wio
    pytest.skip("stub: the implementation stage writes this test")


def test_a_config_with_errors_is_refused(wio: Wio) -> None:
    """AC-4: both views print the error and nothing else, and exit 2."""
    # Given a config with an unknown key
    # When it is listed and shown
    # Then each exits 2 with empty standard output and the error on standard error
    del wio
    pytest.skip("stub: the implementation stage writes this test")
