# SPDX-License-Identifier: Apache-2.0
"""Tests of `wio config` run through the command line with fake ports."""

import io
from dataclasses import dataclass
from typing import TextIO

import pytest

from tests.unit.config.fakes import CONFIG, FakeRepository, MemoryFileSystem
from wio import cli
from wio.cli.table import component_entry
from wio.config import ConfigCommand

TEXT = """
[works]
hierarchy = "nesting"

[stages.define]
goal = "Turn an intent into a Work"
"""


@dataclass
class _Stdio:
    """In-memory standard streams that satisfy the `Stdio` port."""

    stdin: TextIO
    stdout: TextIO
    stderr: TextIO


@dataclass(frozen=True)
class _Ran:
    """What one run wrote and returned."""

    stdout: str
    stderr: str
    code: int


def _run(text: str | None, *argv: str) -> _Ran:
    """Run `wio config ...` on a config held in memory.

    Args:
        text: The content of the config file, or `None` for no file.
        *argv: The arguments after `wio config`.

    Returns:
        The streams and the exit code.
    """
    files = MemoryFileSystem({} if text is None else {CONFIG: text})
    entry = component_entry("config", lambda: ConfigCommand(FakeRepository(), files))
    out, err = io.StringIO(), io.StringIO()
    code = cli.main(["config", *argv], _Stdio(io.StringIO(), out, err), (entry,))
    return _Ran(out.getvalue(), err.getvalue(), code)


def test_bare_config_shows_its_help_and_the_views() -> None:
    """The usage of `wio config` names the subcommands it has."""
    # Given a repository with a valid config

    # When `wio config` runs with no subcommand
    ran = _run(TEXT)

    # Then the usage names list and show and the run succeeds
    assert "usage: wio config" in ran.stdout
    assert "list" in ran.stdout
    assert "show" in ran.stdout
    assert (ran.stderr, ran.code) == ("", 0)


def test_bare_config_needs_no_config_file() -> None:
    """The help does not load the settings."""
    # Given a repository without a config file

    # When `wio config` runs with no subcommand
    ran = _run(None)

    # Then the usage is shown all the same
    assert "usage: wio config" in ran.stdout
    assert ran.code == 0


def test_list_prints_one_line_for_each_setting_with_its_source() -> None:
    """`list` shows the first line of a multi-line goal and the labels."""
    # Given a config that sets a three-line goal
    # When the settings are listed
    # Then the goal's line is shortened and every line is in key-path order
    pytest.skip("stub: the implementation stage writes this test")


def test_list_json_keeps_every_value_whole() -> None:
    """`list --json` maps each key path to its value and source."""
    # Given the same config
    # When the settings are listed as JSON
    # Then the goal is whole and the keys are sorted
    pytest.skip("stub: the implementation stage writes this test")


def test_show_a_setting_prints_its_line_and_its_description() -> None:
    """A single setting is followed by what it is for."""
    # Given a config that sets the hierarchy
    # When the setting is shown
    # Then the line and the description are printed
    pytest.skip("stub: the implementation stage writes this test")


def test_show_a_setting_as_json_is_one_entry() -> None:
    """With `--json` the object holds only that setting."""
    # Given a config that sets the hierarchy
    # When the setting is shown as JSON
    # Then the object has the setting alone
    pytest.skip("stub: the implementation stage writes this test")


def test_show_a_table_prints_its_settings_in_full_without_descriptions() -> None:
    """A table prints the setting lines only, the goal whole."""
    # Given a config with two stages
    # When the stages table is shown
    # Then every setting under it is printed, the goal in full
    pytest.skip("stub: the implementation stage writes this test")


def test_show_the_whole_config_prints_every_setting() -> None:
    """Without a key path every setting is printed."""
    # Given a config
    # When `wio config show` runs
    # Then the output holds the settings of several tables
    pytest.skip("stub: the implementation stage writes this test")


def test_show_a_table_as_json_restricts_the_object_to_it() -> None:
    """Only the key paths under the argument are in the object."""
    # Given a config with two stages
    # When the stages table is shown as JSON
    # Then every key starts with stages
    pytest.skip("stub: the implementation stage writes this test")


def test_show_an_empty_table_prints_nothing_and_succeeds() -> None:
    """A table without settings is not an error."""
    # Given a config without roots
    # When roots are shown, as text and as JSON
    # Then nothing is printed for text and an empty object for JSON
    pytest.skip("stub: the implementation stage writes this test")


def test_show_an_unset_optional_setting_exits_2() -> None:
    """The judge of a stage that has none is not set."""
    # Given a stage without a judge
    # When the judge is shown
    # Then the error says it is not set and nothing is printed
    pytest.skip("stub: the implementation stage writes this test")


def test_show_an_unknown_key_path_exits_2_and_suggests() -> None:
    """A typo gets the closest match."""
    # Given a config with a stage `define`
    # When misspelled key paths are shown
    # Then both exit 2 and name the closest match
    pytest.skip("stub: the implementation stage writes this test")


def test_a_config_with_an_error_is_refused_by_both_views() -> None:
    """Nothing is printed and the error is listed on standard error."""
    # Given a config with an unknown key
    # When it is listed and shown
    # Then each exits 2 with empty standard output and the error
    pytest.skip("stub: the implementation stage writes this test")
