# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio config show`, which shows a setting or a table in full."""

import json
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_show_a_setting_adds_its_description(wio: Wio) -> None:
    """AC-3: a setting prints its line, the description below, and JSON."""
    # Given a config that sets the hierarchy to nesting
    wio.fixture("config/rich")

    # When the setting is shown as text and as JSON
    text = wio.run(["config", "show", "works.hierarchy"])
    as_json = wio.run(["config", "show", "works.hierarchy", "--json"])

    # Then the text has the line and the description, the JSON one entry
    assert text.stdout.splitlines()[0] == 'works.hierarchy = "nesting"  # file'
    assert "How the hierarchy is derived" in text.stdout
    assert json.loads(as_json.stdout) == {
        "works.hierarchy": {"value": "nesting", "source": "file"}
    }


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_show_a_table_and_the_whole_config(wio: Wio) -> None:
    """AC-3: a table and the whole config print their settings in full."""
    # Given a config with two stages, one with a three-line goal
    wio.fixture("config/rich")

    # When the stages and the whole config are shown, and each as JSON
    table = wio.run(["config", "show", "stages"])
    whole = wio.run(["config", "show"])
    table_json = wio.run(["config", "show", "stages", "--json"])
    whole_json = wio.run(["config", "show", "--json"])

    # Then the goal is whole, no description is printed and JSON is restricted
    assert 'stages.define.goal = "Turn an intent\\ninto a Work\\nand stop"' in (
        table.stdout
    )
    assert "What the stage does" not in table.stdout
    assert "works.hierarchy" in whole.stdout
    assert all(key.startswith("stages.") for key in json.loads(table_json.stdout))
    assert "works.hierarchy" in json.loads(whole_json.stdout)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_show_a_table_without_settings_prints_nothing(wio: Wio) -> None:
    """AC-3: a table that holds no setting is not an error."""
    # Given a config without roots
    wio.fixture("config/rich")

    # When the roots are shown, as text and as JSON
    text = wio.run(["config", "show", "roots"])
    as_json = wio.run(["config", "show", "roots", "--json"])

    # Then nothing is printed for text, an empty object for JSON, and both succeed
    assert (text.stdout, text.exit_code) == ("", 0)
    assert (json.loads(as_json.stdout), as_json.exit_code) == ({}, 0)


@pytest.mark.channels(Channel.CLI)
def test_show_an_unset_setting_and_a_list_item_exit_2(wio: Wio) -> None:
    """AC-3: an unset optional setting and an item of a list are refused."""
    # Given a stage without a judge, and a rules_include list
    wio.fixture("config/rich")

    # When the judge and an item of the list are shown
    unset = wio.run(["config", "show", "stages.define.judge"])
    item = wio.run(["config", "show", "stages.define.rules_include[0]"])

    # Then the judge exits 2 saying it is not set, and the item exits 2 naming
    # the list
    assert (unset.exit_code, "not set" in unset.stderr) == (2, True)
    assert item.exit_code == 2
    assert "stages.define.rules_include" in item.stderr


@pytest.mark.channels(Channel.CLI)
def test_show_an_unknown_key_path_suggests_the_closest(wio: Wio) -> None:
    """AC-3: a typo names the closest match and the valid keys."""
    # Given a config with a stage `define`
    wio.fixture("config/rich")

    # When two misspelled key paths are shown
    top = wio.run(["config", "show", "stage.define"])
    entry = wio.run(["config", "show", "stages.definer"])

    # Then both exit 2, the first names the closest match `stages` and the valid
    # top-level keys, and the second names `stages.define` and the stages
    assert (top.exit_code, entry.exit_code) == (2, 2)
    assert "`stages`" in top.stderr
    assert "`stages.define`" in entry.stderr
    assert "`review`" in entry.stderr


@pytest.mark.channels(Channel.CLI)
def test_show_refuses_a_config_with_an_error(wio: Wio) -> None:
    """AC-4: `show` prints nothing and lists the error on standard error."""
    # Given a config with an unknown key
    wio.fixture("config/invalid")

    # When the config is shown
    output = wio.run(["config", "show"])

    # Then it exits 2, standard output is empty and standard error lists the error
    assert output.exit_code == 2
    assert output.stdout == ""
    assert "unknown key `nonsense`" in output.stderr


@pytest.mark.channels(Channel.CLI)
def test_show_outside_a_repository_names_the_directory(
    wio: Wio, sandbox: Sandbox
) -> None:
    """AC-4: `show` in no repository exits 2 and says where to run wio."""
    # Given a directory that is in no git repository

    # When the config is shown
    output = wio.run(["config", "show"])

    # Then it exits 2, prints nothing, and names the directory and what to do
    assert output.exit_code == 2
    assert output.stdout == ""
    assert sandbox.root.name in output.stderr
    assert "run wio from a directory inside the repository" in output.stderr
