# SPDX-License-Identifier: Apache-2.0
"""Tests of how `wio.cli.main` reports the failures of a run."""

import pytest

pytestmark = pytest.mark.skip(reason="architecture stub: the failures leaf")


def test_a_wio_error_exits_two_with_its_message() -> None:
    """A `WioError` at any step is reported as `error:` and its message."""
    # Given four commands, whose describe, configure, wire and run each raise
    # ConfigurationError("no config"), each in an entry with the package
    # "config" and injected functions

    # When main([name], stdio) runs for each

    # Then each returns 2, standard error is "error: no config" and a newline,
    # and standard output is empty


def test_the_message_of_a_wio_error_is_plain_on_a_terminal() -> None:
    """Standard error holds no escape character, whatever the color rules say."""
    # Given standard error on a pseudo-terminal from os.openpty and
    # FORCE_COLOR=1, and a command whose run raises ConfigurationError("no
    # config")

    # When main runs it

    # Then standard error is exactly "error: no config" and a newline, with no
    # escape character


def test_a_bug_exits_seventy_with_its_traceback() -> None:
    """An exception that is not a `WioError` is reported with its traceback."""
    # Given four commands, whose describe, configure, wire and run each raise a
    # RuntimeError with the message boom

    # When main([name], stdio) runs for each

    # Then each returns 70, standard output is empty, and the last line of
    # standard error is "RuntimeError: boom"


def test_an_exit_code_outside_zero_and_one_is_a_bug() -> None:
    """A `run` that returns 3 is reported with the command and the code."""
    # Given a command whose run returns 3

    # When main runs it

    # Then it returns 70, standard output is empty, and standard error names the
    # command and the code 3


def test_the_core_writes_only_to_stdio() -> None:
    """The process's own streams hold nothing, whatever happens in a run."""
    # Given in-memory stdio and the process's sys.stdout and sys.stderr captured

    # When main runs --help, --version, an unknown subcommand and three
    # commands, one raising a WioError, one raising RuntimeError and one
    # returning 3

    # Then the process's streams hold nothing, and the output is in stdio
