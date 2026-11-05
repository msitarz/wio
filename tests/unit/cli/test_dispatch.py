# SPDX-License-Identifier: Apache-2.0
"""Tests of the dispatch of `wio.cli.main` to the entries of the table."""

import pytest

pytestmark = pytest.mark.skip(reason="architecture stub: the dispatch leaf")


def test_bare_and_help_print_the_summary_and_the_commands_by_name() -> None:
    """Bare `wio` and `--help` give the same output, in order of name."""
    # Given a table of entries zeta and alpha, built with injected describe and
    # wire functions, with help texts

    # When main([], stdio) and main(["--help"], stdio) run

    # Then both return 0 with the same standard output, which holds the Summary,
    # then the help text of alpha before that of zeta; standard error is empty


def test_the_help_of_a_subcommand_wires_nothing() -> None:
    """`wio ok --help` names the options of `ok` and does not wire it."""
    # Given a table with the entry ok, which takes --flag, and a wire that
    # records its call

    # When main(["ok", "--help"], stdio) runs

    # Then it returns 0, standard output names --flag, and wire was not called


def test_version_prints_the_version_of_the_distribution() -> None:
    """`--version` prints `wio <version>` and a newline."""
    # Given the synchronized environment

    # When main(["--version"], stdio) runs

    # Then it returns 0, standard output is wio, a space, the version from
    # importlib.metadata and a newline, and standard error is empty


def test_only_the_chosen_command_is_wired_once() -> None:
    """The `wire` of an entry runs once, for the subcommand that was chosen."""
    # Given a table of ok and no, each with a wire that records its call

    # When main(["ok"], stdio) runs, then bare, --help and --version

    # Then ok was wired exactly once, no never, the last three called no wire,
    # and the describe of both entries ran every time


def test_a_commands_exit_code_is_the_runs() -> None:
    """A command that returns 0 or 1 sets the exit code and gets its arguments."""
    # Given a table of ok, which returns 0, and no, which returns 1, with ok
    # taking --flag

    # When main(["ok", "--flag"], stdio) and main(["no"], stdio) run

    # Then they return 0 and 1, and ok received --flag in its arguments


def test_a_usage_mistake_exits_two() -> None:
    """An unknown subcommand or option exits 2 with argparse's message."""
    # Given a table with the entry ok

    # When main(["nope"], stdio), main(["--nope"], stdio) and
    # main(["ok", "--bad"], stdio) run

    # Then each returns 2 without raising, standard output is empty and standard
    # error names the unknown word


def test_the_output_is_plain_when_the_streams_are_not_terminals() -> None:
    """In-memory streams get no escape character, and the usage names `wio`."""
    # Given in-memory stdio and an environment without PYTHON_COLORS, NO_COLOR
    # or FORCE_COLOR

    # When main([], stdio) and main(["nope"], stdio) run

    # Then neither stream holds an escape character, and every usage line starts
    # with the program name wio


def test_the_help_is_colored_on_a_terminal_unless_no_color_is_set() -> None:
    """Python's color rules decide the color of the help on a terminal."""
    # Given standard output on a pseudo-terminal from os.openpty, and the same
    # environment

    # When main(["--help"], stdio) runs, then again with NO_COLOR=1

    # Then the first output holds an escape character and the second holds none
