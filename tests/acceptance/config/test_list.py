# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio config list`, which shows every setting on a line."""

from json import loads
from typing import TYPE_CHECKING

from tests.acceptance.channels import CLI_ONLY, IN_BOTH

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox


@IN_BOTH
def test_list_shortens_the_lines_and_labels_the_sources(wio: Wio) -> None:
    """AC-2: each setting is a line of at most 80 columns, in key-path order."""
    # Given a config with a three-line goal and a ninety-character description
    wio.fixture("config/rich")

    # When the settings are listed
    output = wio.run(["config", "list"])

    # Then the goal shows its first line, every line fits and the order is sorted
    lines = output.stdout.splitlines()
    assert 'stages.define.goal = "Turn an intent…"  # file' in lines
    assert 'stages.define.session = "any"  # default' in lines
    assert all(len(line) <= 80 for line in lines)
    assert lines == sorted(lines)
    assert output.exit_code == 0


@IN_BOTH
def test_list_keeps_a_long_key_whole(wio: Wio) -> None:
    """AC-2: a key path and a label that reach 80 columns leave `…` for the value."""
    # Given a stage whose name makes the key path and the label reach 80 columns
    wio.fixture("config/long-key")

    # When the settings are listed
    output = wio.run(["config", "list"])

    # Then its goal shows as an ellipsis, with the key path and label whole
    name = "n" * 62
    assert f"stages.{name}.goal = …  # file" in output.stdout.splitlines()


@IN_BOTH
def test_list_json_keeps_every_value(wio: Wio) -> None:
    """AC-2: the JSON object maps each key path to its value and source."""
    # Given the config with the three-line goal and the long description
    wio.fixture("config/rich")

    # When the settings are listed as JSON
    output = wio.run(["config", "list", "--json"])

    # Then values are whole and the keys are sorted
    found = loads(output.stdout)
    goal = "Turn an intent\ninto a Work\nand stop"
    assert found["stages.define.goal"] == {"value": goal, "source": "file"}
    assert found["actions.define.description"]["value"] == "a" * 90
    assert list(found) == sorted(found)


@CLI_ONLY
def test_list_refuses_a_config_with_an_error(wio: Wio) -> None:
    """AC-4: `list` prints nothing and lists the error on standard error."""
    # Given a config with an unknown key
    wio.fixture("config/invalid")

    # When the settings are listed
    output = wio.run(["config", "list"])

    # Then it exits 2, standard output is empty and standard error lists the error
    assert output.exit_code == 2
    assert output.stdout == ""
    assert "unknown key `nonsense`" in output.stderr


@CLI_ONLY
def test_list_outside_a_repository_names_the_directory(
    wio: Wio, sandbox: Sandbox
) -> None:
    """AC-4: `list` in no repository exits 2 and says where to run wio."""
    # Given a directory that is in no git repository

    # When the settings are listed
    output = wio.run(["config", "list"])

    # Then it exits 2, prints nothing, and names the directory and what to do
    assert output.exit_code == 2
    assert output.stdout == ""
    assert sandbox.root.name in output.stderr
    assert "run wio from a directory inside the repository" in output.stderr
