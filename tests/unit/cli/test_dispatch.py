# SPDX-License-Identifier: Apache-2.0
"""Tests of the dispatch of `wio.cli.main` to the entries of the table."""

import argparse
import importlib.metadata
from typing import TYPE_CHECKING

import pytest

from tests.unit.cli.fakes import Fake, Spec, run_main, run_on_terminal
from wio.cli import dispatch

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Sequence


COLOR_VARIABLES = ("PYTHON_COLORS", "NO_COLOR", "FORCE_COLOR")


def _summary() -> str:
    """Read the `Summary` of the distribution.

    Returns:
        The summary line of the package metadata.
    """
    return importlib.metadata.metadata("work-it-out")["Summary"]


def _plain(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove the variables that force or forbid color, and make TERM a terminal.

    Args:
        monkeypatch: The test's monkeypatch fixture.
    """
    for name in COLOR_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("TERM", "xterm")


def test_bare_and_help_print_the_summary_and_the_commands_by_name() -> None:
    """Bare `wio` and `--help` give the same output, in order of name."""
    # Given a table of entries zeta and alpha, built with injected describe and
    # wire functions, with help texts
    table = [
        Fake(Spec("zeta", "The last one.")).entry(),
        Fake(Spec("alpha", "The first one.")).entry(),
    ]

    # When the command runs bare and with --help
    bare, helped = run_main([], table), run_main(["--help"], table)

    # Then both return 0 with the same standard output, which holds the Summary,
    # then the help text of alpha before that of zeta; standard error is empty
    code, text, err = bare
    assert (code, helped[0]) == (0, 0)
    assert text == helped[1]
    assert text.index(_summary()) < text.index("The first one.")
    assert text.index("The first one.") < text.index("The last one.")
    assert (err, helped[2]) == ("", "")


def test_the_help_of_a_subcommand_wires_nothing() -> None:
    """`wio ok --help` names the options of `ok` and does not wire it."""
    # Given a table with the entry ok, which takes --flag, and a wire that
    # records its call
    ok = Fake(Spec("ok", "Works.", flag=True))

    # When the command ok runs with --help
    code, out, _ = run_main(["ok", "--help"], [ok.entry()])

    # Then it returns 0, standard output names --flag, and wire was not called
    assert code == 0
    assert "--flag" in out
    assert ok.wired == 0


def test_version_prints_the_version_of_the_distribution() -> None:
    """`--version` prints `wio <version>` and a newline."""
    # Given the synchronized environment

    # When the command runs with --version
    code, out, err = run_main(["--version"], [])

    # Then it returns 0, standard output is wio, a space, the installed
    # version and a newline, and standard error is empty
    version = importlib.metadata.version("work-it-out")
    assert (code, out, err) == (0, f"wio {version}\n", "")


def test_only_the_chosen_command_is_wired_once() -> None:
    """The `wire` of an entry runs once, for the subcommand that was chosen."""
    # Given a table of ok and no, each with a wire that records its call
    ok, no = Fake(Spec("ok", "Works.")), Fake(Spec("no", "Fails."))
    table = [ok.entry(), no.entry()]

    # When the command ok runs, then bare, with --help and with --version
    run_main(["ok"], table)
    wired_after_ok = (ok.wired, no.wired)
    others: list[list[str]] = [[], ["--help"], ["--version"]]
    for argv in others:
        run_main(argv, table)

    # Then ok was wired exactly once, no never, the last three called no wire,
    # and the describe of both entries ran every time
    assert wired_after_ok == (1, 0)
    assert (ok.wired, no.wired) == (1, 0)
    assert (ok.described, no.described) == (4, 4)


def test_a_commands_exit_code_is_the_runs() -> None:
    """A command that returns 0 or 1 sets the exit code and gets its arguments."""
    # Given a table of ok, which returns 0, and no, which returns 1, with ok
    # taking --flag
    ok = Fake(Spec("ok", "Works.", flag=True), code=0)
    no = Fake(Spec("no", "Fails."), code=1)
    table = [ok.entry(), no.entry()]

    # When the command ok runs with --flag and the command no runs
    codes = run_main(["ok", "--flag"], table)[0], run_main(["no"], table)[0]

    # Then they return 0 and 1, and ok received --flag in its arguments
    assert codes == (0, 1)
    assert [args.flag for args in ok.received] == [True]


@pytest.mark.parametrize(
    ("argv", "word"),
    [(["nope"], "nope"), (["--nope"], "--nope"), (["ok", "--bad"], "--bad")],
)
def test_a_usage_mistake_exits_two(argv: list[str], word: str) -> None:
    """An unknown subcommand or option exits 2 with argparse's message."""
    # Given a table with the entry ok
    table = [Fake(Spec("ok", "Works.")).entry()]

    # When the command runs with a mistake
    code, out, err = run_main(argv, table)

    # Then it returns 2 without raising, standard output is empty and standard
    # error names the unknown word
    assert (code, out) == (2, "")
    assert word in err


def test_the_output_is_plain_when_the_streams_are_not_terminals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """In-memory streams get no escape character, and the usage names `wio`."""
    # Given in-memory stdio and an environment without PYTHON_COLORS, NO_COLOR
    # or FORCE_COLOR
    _plain(monkeypatch)
    table = [Fake(Spec("ok", "Works.")).entry()]

    # When the command runs bare and with an unknown command
    _, out, _ = run_main([], table)
    _, _, err = run_main(["nope"], table)

    # Then neither stream holds an escape character, and every usage line starts
    # with the program name wio
    usages = [line for line in out.splitlines() + err.splitlines() if "usage" in line]
    assert "\x1b" not in out + err
    assert usages
    assert all(line.startswith("usage: wio") for line in usages)


def test_the_help_is_colored_on_a_terminal_unless_no_color_is_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Python's color rules decide the color of the help on a terminal."""
    # Given standard output on a pseudo-terminal, and the same
    # environment
    _plain(monkeypatch)

    # When the command runs with --help, then again with NO_COLOR=1
    colored = run_on_terminal(["--help"], [], "stdout")
    monkeypatch.setenv("NO_COLOR", "1")
    plain = run_on_terminal(["--help"], [], "stdout")

    # Then the first output holds an escape character and the second holds none
    assert "\x1b" in colored
    assert "\x1b" not in plain


class _Exiting(argparse.ArgumentParser):
    """A parser that stops with a fixed `SystemExit` code."""

    def __init__(self, code: object) -> None:
        """Remember the code to exit with.

        Args:
            code: The code of the `SystemExit` to raise.
        """
        super().__init__(prog="wio")
        self.stop = code

    def parse_args(  # type: ignore[override]
        self, args: Sequence[str] | None = None, namespace: object = None
    ) -> Namespace:
        """Stop instead of parsing.

        Args:
            args: Ignored.
            namespace: Ignored.

        Raises:
            SystemExit: Always, with the code this parser was made with.
        """
        del args, namespace
        raise SystemExit(self.stop)


@pytest.mark.parametrize(
    ("code", "expected"), [(None, 0), (0, 0), (2, 2), ("a message", 1)]
)
def test_an_exit_of_the_parser_becomes_the_exit_code(
    code: object, expected: int
) -> None:
    """A missing code is success, an integer stays and a message is a failure."""
    # Given a parser that exits with a code
    parser = _Exiting(code)

    # When the arguments are parsed
    result = dispatch.parse(parser, [])

    # Then the result is the exit code
    assert result == expected
