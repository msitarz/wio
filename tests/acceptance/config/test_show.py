# SPDX-License-Identifier: Apache-2.0
"""Scenarios of the Work that shows the settings: `wio config list` and `show`."""

import json
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

GOAL = "Turn an intent\ninto a Work\nand stop"
ACTION = "a" * 90
CONFIG = f'''
[works]
hierarchy = "nesting"

[actions.define]
description = "{ACTION}"

[stages.define]
goal = """{GOAL}"""
rules_include = ["py.ARC001"]

[stages.review]
skill = "review"
'''

# Git runs in every scenario, so none of them is fast.
pytestmark = [
    pytest.mark.slow,
    pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI),
]


def test_bare_config_shows_the_help(wio: Wio) -> None:
    """AC-1: bare `wio config` names its subcommands and exits 0."""
    # Given a repository with a valid config
    wio.with_config(CONFIG)

    # When `wio config` runs
    output = wio.run_config()

    # Then the output names list and show and the exit code is 0
    assert "list" in output.stdout
    assert "show" in output.stdout
    assert output.exit_code == 0


def test_list_shortens_the_lines_and_labels_the_sources(wio: Wio) -> None:
    """AC-2: each setting is a line of at most 80 columns, in key-path order."""
    # Given a config with a three-line goal and a ninety-character description
    wio.with_config(CONFIG)

    # When the settings are listed
    output = wio.run_config("list")

    # Then the goal shows its first line, every line fits and the order is sorted
    lines = output.stdout.splitlines()
    assert 'stages.define.goal = "Turn an intent…"  # file' in lines
    assert 'stages.define.session = "any"  # default' in lines
    assert all(len(line) <= 80 for line in lines)
    assert lines == sorted(lines)
    assert output.exit_code == 0


def test_list_keeps_a_long_key_whole(wio: Wio) -> None:
    """AC-2: a key path and a label that reach 80 columns leave `…` for the value."""
    # Given a stage whose name makes the key path and the label reach 80 columns
    name = "n" * 62
    wio.with_config(f'[stages.{name}]\ngoal = "g"\n')

    # When the settings are listed
    output = wio.run_config("list")

    # Then its goal shows as an ellipsis, with the key path and label whole
    expected = f"stages.{name}.goal = …  # file"
    assert expected in output.stdout.splitlines()


def test_list_json_keeps_every_value(wio: Wio) -> None:
    """AC-2: the JSON object maps each key path to its value and source."""
    # Given the same config
    wio.with_config(CONFIG)

    # When the settings are listed as JSON
    output = wio.run_config("list", "--json")

    # Then values are whole and the keys are sorted
    found = json.loads(output.stdout)
    assert found["stages.define.goal"] == {"value": GOAL, "source": "file"}
    assert found["actions.define.description"]["value"] == ACTION
    assert list(found) == sorted(found)


def test_show_a_setting_adds_its_description(wio: Wio) -> None:
    """AC-3: a setting prints its line, the description below and JSON."""
    # Given a config that sets the hierarchy to nesting
    wio.with_config(CONFIG)

    # When the setting is shown as text and as JSON
    text = wio.run_config("show", "works.hierarchy")
    as_json = wio.run_config("show", "works.hierarchy", "--json")

    # Then the text has the line and the description, the JSON one entry
    assert text.stdout.splitlines()[0] == 'works.hierarchy = "nesting"  # file'
    assert "How the hierarchy is derived" in text.stdout
    assert json.loads(as_json.stdout) == {
        "works.hierarchy": {"value": "nesting", "source": "file"}
    }


def test_show_a_table_and_the_whole_config(wio: Wio) -> None:
    """AC-3: a table and the whole config print their settings in full."""
    # Given a config with two stages, one with a three-line goal
    wio.with_config(CONFIG)

    # When the stages and the whole config are shown, and each as JSON
    table = wio.run_config("show", "stages")
    whole = wio.run_config("show")
    as_json = wio.run_config("show", "stages", "--json")
    whole_json = wio.run_config("show", "--json")

    # Then the goal is whole, no description is printed and JSON is restricted
    assert 'stages.define.goal = "Turn an intent\\ninto a Work\\nand stop"' in (
        table.stdout
    )
    assert "What the stage does" not in table.stdout
    assert "works.hierarchy" in whole.stdout
    assert all(key.startswith("stages.") for key in json.loads(as_json.stdout))
    assert "works.hierarchy" in json.loads(whole_json.stdout)


def test_show_unset_empty_and_inside_a_list(wio: Wio) -> None:
    """AC-3: an unset setting and a list item exit 2, an empty table exits 0."""
    # Given a stage without a judge, no roots and a rules_include list
    wio.with_config(CONFIG)

    # When each is shown
    unset = wio.run_config("show", "stages.define.judge")
    empty = wio.run_config("show", "roots")
    empty_json = wio.run_config("show", "roots", "--json")
    item = wio.run_config("show", "stages.define.rules_include[0]")

    # Then the judge exits 2 saying it is not set, roots print nothing and exit 0
    # (an empty object with --json), and the list item exits 2 naming the list
    assert (unset.exit_code, "not set" in unset.stderr) == (2, True)
    assert (empty.exit_code, empty.stdout) == (0, "")
    assert json.loads(empty_json.stdout) == {}
    assert item.exit_code == 2
    assert "stages.define.rules_include" in item.stderr


def test_show_an_unknown_key_path_suggests_the_closest(wio: Wio) -> None:
    """AC-3: a typo names the closest match and the valid keys."""
    # Given a config with a stage `define`
    wio.with_config(CONFIG)

    # When two misspelled key paths are shown
    top = wio.run_config("show", "stage.define")
    entry = wio.run_config("show", "stages.definer")

    # Then both exit 2, the first names the closest match `stages` and the valid
    # top-level keys, and the second names `stages.define` and the stages
    assert (top.exit_code, entry.exit_code) == (2, 2)
    assert "`stages`" in top.stderr
    assert "`stages.define`" in entry.stderr
    assert "`review`" in entry.stderr


def test_a_config_with_errors_is_refused(wio: Wio) -> None:
    """AC-4: both views print the error and nothing else, and exit 2."""
    # Given a config with an unknown key
    wio.with_config("[works]\nnonsense = 1\n")

    # When it is listed and shown
    listed = wio.run_config("list")
    shown = wio.run_config("show")

    # Then each exits 2 with empty standard output and the error on standard error
    for output in (listed, shown):
        assert output.exit_code == 2
        assert output.stdout == ""
        assert "unknown key `nonsense`" in output.stderr
