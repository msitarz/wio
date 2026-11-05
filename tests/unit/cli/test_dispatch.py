# SPDX-License-Identifier: Apache-2.0
"""Tests of the dispatch of `wio.cli.main` to the entries of the table."""

import importlib.metadata
import io
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, TextIO

import pytest

from wio import cli
from wio.cli.table import Entry

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from wio.cli.ports import Command, CommandSpec
    from wio.io.ports import Stdio

PYPROJECT = Path(__file__).resolve().parents[3] / "pyproject.toml"
COLOR_VARIABLES = ("PYTHON_COLORS", "NO_COLOR", "FORCE_COLOR")


@dataclass
class FakeStdio:
    """In-memory standard streams that satisfy the `Stdio` port."""

    stdin: TextIO = field(default_factory=io.StringIO)
    stdout: TextIO = field(default_factory=io.StringIO)
    stderr: TextIO = field(default_factory=io.StringIO)


@dataclass
class Spec:
    """A command spec with a name, a help text and an optional `--flag`."""

    name: str
    help: str
    flag: bool = False

    def configure(self, parser: ArgumentParser) -> None:
        """Add `--flag` to the subparser when the spec has one.

        Args:
            parser: The subparser of the command.
        """
        if self.flag:
            parser.add_argument("--flag", action="store_true")


@dataclass
class Fake:
    """A command that counts how often it is described, wired and run."""

    spec: Spec
    code: int = 0
    described: int = 0
    wired: int = 0
    received: list[Namespace] = field(default_factory=list)

    def entry(self) -> Entry:
        """Make the table entry for this fake, under the package `config`.

        Returns:
            An entry whose functions count their calls.
        """
        return Entry(package="config", describe=self.describe, wire=self.wire)

    def describe(self) -> CommandSpec:
        """Count the call and return the spec.

        Returns:
            The spec of the fake.
        """
        self.described += 1
        return self.spec

    def wire(self) -> Command:
        """Count the call and return the fake as the command.

        Returns:
            This fake.
        """
        self.wired += 1
        return self

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Remember the arguments and answer with the fixed code.

        Args:
            args: The parsed arguments.
            stdio: Ignored.

        Returns:
            The exit code this fake was made with.
        """
        del stdio
        self.received.append(args)
        return self.code


def _run(argv: list[str], table: list[Entry]) -> tuple[int, str, str]:
    """Run `main` on in-memory streams.

    Args:
        argv: The arguments after the program name.
        table: The entries of the subcommands.

    Returns:
        The exit code, standard output and standard error.
    """
    out, err = io.StringIO(), io.StringIO()
    code = cli.main(argv, FakeStdio(stdout=out, stderr=err), table)
    return code, out.getvalue(), err.getvalue()


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

    # When main([], stdio) and main(["--help"], stdio) run
    bare, helped = _run([], table), _run(["--help"], table)

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

    # When main(["ok", "--help"], stdio) runs
    code, out, _ = _run(["ok", "--help"], [ok.entry()])

    # Then it returns 0, standard output names --flag, and wire was not called
    assert code == 0
    assert "--flag" in out
    assert ok.wired == 0


def test_version_prints_the_version_of_the_distribution() -> None:
    """`--version` prints `wio <version>` and a newline."""
    # Given the synchronized environment

    # When main(["--version"], stdio) runs
    code, out, err = _run(["--version"], [])

    # Then it returns 0, standard output is wio, a space, the version from
    # importlib.metadata and a newline, and standard error is empty
    version = importlib.metadata.version("work-it-out")
    assert (code, out, err) == (0, f"wio {version}\n", "")


def test_only_the_chosen_command_is_wired_once() -> None:
    """The `wire` of an entry runs once, for the subcommand that was chosen."""
    # Given a table of ok and no, each with a wire that records its call
    ok, no = Fake(Spec("ok", "Works.")), Fake(Spec("no", "Fails."))
    table = [ok.entry(), no.entry()]

    # When main(["ok"], stdio) runs, then bare, --help and --version
    _run(["ok"], table)
    wired_after_ok = (ok.wired, no.wired)
    others: list[list[str]] = [[], ["--help"], ["--version"]]
    for argv in others:
        _run(argv, table)

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

    # When main(["ok", "--flag"], stdio) and main(["no"], stdio) run
    codes = _run(["ok", "--flag"], table)[0], _run(["no"], table)[0]

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

    # When main runs with a mistake
    code, out, err = _run(argv, table)

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

    # When main([], stdio) and main(["nope"], stdio) run
    _, out, _ = _run([], table)
    _, _, err = _run(["nope"], table)

    # Then neither stream holds an escape character, and every usage line starts
    # with the program name wio
    usages = [line for line in out.splitlines() + err.splitlines() if "usage" in line]
    assert "\x1b" not in out + err
    assert usages
    assert all(line.startswith("usage: wio") for line in usages)


def _help_on_a_terminal() -> str:
    """Run `wio --help` with standard output on a pseudo-terminal.

    Returns:
        What `main` wrote to the terminal.
    """
    master, slave = os.openpty()
    try:
        with os.fdopen(slave, "w") as terminal:
            cli.main(["--help"], FakeStdio(stdout=terminal), [])
            terminal.flush()
            return os.read(master, 65536).decode()
    finally:
        os.close(master)


def test_the_help_is_colored_on_a_terminal_unless_no_color_is_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Python's color rules decide the color of the help on a terminal."""
    # Given standard output on a pseudo-terminal from os.openpty, and the same
    # environment
    _plain(monkeypatch)

    # When main(["--help"], stdio) runs, then again with NO_COLOR=1
    colored = _help_on_a_terminal()
    monkeypatch.setenv("NO_COLOR", "1")
    plain = _help_on_a_terminal()

    # Then the first output holds an escape character and the second holds none
    assert "\x1b" in colored
    assert "\x1b" not in plain
