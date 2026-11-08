# SPDX-License-Identifier: Apache-2.0
"""Tests of how `wio.cli.main` reports the failures of a run."""

import io
from typing import TYPE_CHECKING

import pytest

from tests.unit.cli.fakes import Fake, FakeStdio, Spec, run_main, run_on_terminal
from wio import cli
from wio.errors import ConfigurationError

if TYPE_CHECKING:
    from wio.cli.table import Entry

STEPS = ("describe", "configure", "wire", "run")


@pytest.mark.parametrize("step", STEPS)
def test_a_wio_error_exits_two_with_its_message(step: str) -> None:
    """A `WioError` at any step is reported as `error:` and its message."""
    # Given four commands, whose describe, configure, wire and run each raise
    # a configuration error saying "no config", each in an entry with the package
    # "config" and injected functions
    message = "no config"
    table = [Fake.failing(step, ConfigurationError(message)).entry()]

    # When each command runs
    code, out, err = run_main(["failing"], table)

    # Then each returns 2, standard error is "error: no config" and a newline,
    # and standard output is empty
    assert (code, out, err) == (2, "", "error: no config\n")


def test_the_message_of_a_wio_error_is_plain_on_a_terminal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Standard error holds no escape character, whatever the color rules say."""
    # Given standard error on a pseudo-terminal and FORCE_COLOR=1, and a command
    # whose run raises a configuration error saying "no config"
    monkeypatch.setenv("FORCE_COLOR", "1")
    message = "no config"
    table = [Fake.failing("run", ConfigurationError(message)).entry()]

    # When the command runs it
    written = run_on_terminal(["failing"], table, "stderr")

    # Then standard error is exactly "error: no config" and a newline, with no
    # escape character
    assert "\x1b" not in written
    assert written.replace("\r\n", "\n") == "error: no config\n"


@pytest.mark.parametrize("step", STEPS)
def test_a_bug_exits_seventy_with_its_traceback(step: str) -> None:
    """An exception that is not a `WioError` is reported with its traceback."""
    # Given four commands, whose describe, configure, wire and run each raise a
    # RuntimeError with the message boom
    message = "boom"
    table = [Fake.failing(step, RuntimeError(message)).entry()]

    # When each command runs
    code, out, err = run_main(["failing"], table)

    # Then each returns 70, standard output is empty, and the last line of
    # standard error is "RuntimeError: boom"
    assert (code, out) == (70, "")
    assert err.splitlines()[-1] == "RuntimeError: boom"


def test_an_exit_code_outside_zero_and_one_is_a_bug() -> None:
    """A `run` that returns 3 is reported with the command and the code."""
    # Given a command whose run returns 3
    table = [Fake(Spec("odd", "Returns 3."), code=3).entry()]

    # When the command runs it
    code, out, err = run_main(["odd"], table)

    # Then it returns 70, standard output is empty, and standard error names the
    # command and the code 3
    assert (code, out) == (70, "")
    assert "odd" in err
    assert "3" in err


def test_the_core_writes_only_to_stdio(capsys: pytest.CaptureFixture[str]) -> None:
    """The process's own streams hold nothing, whatever happens in a run."""
    # Given in-memory stdio and the process's own standard output and error captured
    table: list[Entry] = [
        Fake.failing("run", ConfigurationError("no config"), "wio-error").entry(),
        Fake.failing("run", RuntimeError("boom"), "bug").entry(),
        Fake(Spec("odd", "Returns 3."), code=3).entry(),
    ]
    out, err = io.StringIO(), io.StringIO()
    stdio = FakeStdio(stdout=out, stderr=err)

    # When the command runs --help, --version, an unknown subcommand and three
    # commands, one raising a WioError, one raising RuntimeError and one
    # returning 3
    for argv in (["--help"], ["--version"], ["nope"], ["wio-error"], ["bug"], ["odd"]):
        cli.main(argv, stdio, table)

    # Then the process's streams hold nothing, and the output is in stdio
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", "")
    assert out.getvalue()
    assert err.getvalue()
