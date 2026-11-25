# SPDX-License-Identifier: Apache-2.0
"""Tests of the shell of `wio context`, with a fake compiler."""

from dataclasses import replace
from typing import TYPE_CHECKING

import pytest

from tests.fakes import FakeEnvironment, value_or_raise
from tests.unit.cli.fakes import run_main
from tests.unit.fakes import ROOT, FakeRepository, MemoryFileSystem
from wio.cli.table import COMMANDS, Entry
from wio.context import (
    Compiled,
    CompiledBundle,
    ContextCommand,
    Services,
    describe,
)
from wio.errors import WioError

if TYPE_CHECKING:
    from collections.abc import Callable

    from wio.cli.ports import Command

_PENDING = pytest.mark.xfail(strict=True)
_ARGV = ["context", "k3m9xq", "deliver", "architecture"]


def _compiled() -> Compiled:
    """Build a result with two rules and two warnings that are not sorted.

    Returns:
        The result.
    """
    bundle = CompiledBundle(
        "the bundle\n", "4f3a9c01b2d7", 11, {"a.A001": "1", "b.B001": "2"}
    )
    return Compiled(bundle, ("zulu thing", "alpha thing"))


def _command(
    result: Compiled | Exception, asked: list[tuple[str, str, str]] | None = None
) -> Command:
    """Build the command over fakes.

    Args:
        result: What the fake compiler returns or raises.
        asked: Takes the arguments of each compilation when given.

    Returns:
        The command.
    """

    def compiler(work_id: str, action: str, stage: str) -> Compiled:
        """Record the arguments and give the configured result.

        Args:
            work_id: The Work's id.
            action: The action.
            stage: The stage.

        Returns:
            The result.

        Raises:
            Exception: The configured error.
        """
        if asked is not None:
            asked.append((work_id, action, stage))
        return value_or_raise(result)

    services = Services(FakeRepository(), MemoryFileSystem(), FakeEnvironment(ROOT))
    return ContextCommand(services, compiler)


def _entry(wire: Callable[[], Command]) -> Entry:
    """Make an entry that describes the real command.

    Args:
        wire: What the entry wires.

    Returns:
        The entry.
    """
    return Entry(package="context", describe=describe, wire=wire)


def _real_entry() -> Entry:
    """Find the entry of `context` in the real table.

    Returns:
        The entry.

    Raises:
        ValueError: If the table has none, or more than one.
    """
    (entry,) = (item for item in COMMANDS if item.package == "context")
    return entry


def test_the_help_of_wio_lists_context() -> None:
    """AC-1: `wio --help` lists `context` with its description."""
    # Given the entry of `context` in the table
    entry = _real_entry()

    # When `wio --help` runs
    code, out, _ = run_main(["--help"], [entry])

    # Then it lists `context` with its one line and exits 0
    assert code == 0
    assert "context" in out
    assert describe().help in " ".join(out.split())


def test_the_usage_names_the_work_the_action_and_the_stage() -> None:
    """AC-1: with no argument the usage names the three and the exit code is 2."""
    # Given the entry of `context` in the table
    entry = _real_entry()

    # When `wio context` runs with no argument
    code, out, err = run_main(["context"], [entry])

    # Then a usage line naming them is on standard error and it exits 2
    assert (code, out) == (2, "")
    usage = " ".join(err.split())
    assert "usage: wio context " in usage
    assert "<work> <action> <stage>" in usage


@_PENDING
def test_the_bundle_goes_to_standard_output_and_the_warnings_are_reported() -> None:
    """AC-2: the text alone on standard output, one line for each warning."""
    # Given a fake compiler that returns a text, rules and two warnings
    asked: list[tuple[str, str, str]] = []
    entry = _entry(lambda: _command(_compiled(), asked))

    # When `wio context k3m9xq deliver architecture` runs
    code, out, err = run_main(_ARGV, [entry])

    # Then the output is the text, each warning is a line, and it exits 0
    assert (code, out) == (0, "the bundle\n")
    assert err == "warning: zulu thing\nwarning: alpha thing\n"
    assert asked == [("k3m9xq", "deliver", "architecture")]


@_PENDING
@pytest.mark.parametrize(
    ("error", "expected"),
    [(WioError("cannot go on"), 2), (ValueError("broken"), 70)],
    ids=["mistake", "bug"],
)
def test_failures_map_to_exit_codes(error: Exception, expected: int) -> None:
    """AC-3: a `WioError` exits 2 with its message, and anything else 70."""
    # Given a compiler that raises the error
    asked: list[tuple[str, str, str]] = []
    entry = _entry(lambda: _command(error, asked))

    # When the command runs
    code, out, err = run_main(_ARGV, [entry])

    # Then the compiler was asked, nothing is on standard output and the exit code
    # fits the error
    assert len(asked) == 1
    assert (code, out) == (expected, "")
    assert (err == "error: cannot go on\n") is (expected == 2)


def test_only_a_run_wires_the_command_and_wires_it_once() -> None:
    """AC-5: the help does not wire `context`, and a run does it once."""
    # Given the entry of the table with a `wire` that records its calls
    wired: list[None] = []

    def wire() -> Command:
        """Count the call and build the command.

        Returns:
            The command.
        """
        wired.append(None)
        return _command(_compiled())

    entry = replace(_real_entry(), wire=wire)

    # When `wio --help` runs and then `wio context` runs with its arguments
    run_main(["--help"], [entry])
    after_help = len(wired)
    run_main(_ARGV, [entry])

    # Then the help did not call `wire` and the run called it once
    assert (after_help, len(wired)) == (0, 1)
