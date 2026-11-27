# SPDX-License-Identifier: Apache-2.0
"""Tests of the shell of `wio context`, with a fake compiler."""

from dataclasses import replace
from typing import TYPE_CHECKING, override

import pytest

from tests.fakes import FakeEnvironment, ReviewedCommitFake, value_or_raise
from tests.unit.cli.fakes import run_main
from tests.unit.context.fakes import EventSinkFake, SettingsStub
from tests.unit.fakes import ROOT, FakeDirectories, FakeRepository, MemoryFileSystem
from wio.cli.table import COMMANDS, Entry
from wio.context import (
    Compiled,
    CompiledBundle,
    ContextCommand,
    Services,
    describe,
)
from wio.errors import WioError
from wio.models.config import Bundle, Config

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from wio.cli.ports import Command

_ARGV = ["context", "k3m9xq", "deliver", "architecture"]


def _compiled() -> Compiled:
    """Build a result with two rules and warnings, unsorted and one repeated.

    Returns:
        The result.
    """
    bundle = CompiledBundle(
        "the bundle\n\n", "4f3a9c01b2d7", 12, {"a.A001": "1", "b.B001": "2"}
    )
    return Compiled(bundle, ("zulu thing", "alpha thing", "zulu thing"))


def _command(
    result: Compiled | Exception, asked: list[tuple[str, str, str]] | None = None
) -> ContextCommand:
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

    services = Services(
        FakeRepository(),
        MemoryFileSystem(),
        FakeEnvironment(ROOT),
        FakeDirectories(ROOT),
        SettingsStub(Config()),
        EventSinkFake(),
        ReviewedCommitFake(),
    )
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


def test_the_bundle_goes_to_standard_output_and_the_warnings_are_reported() -> None:
    """AC-2: the text alone on standard output, one line for each warning."""
    # Given a fake compiler that returns a text, rules and two warnings
    asked: list[tuple[str, str, str]] = []
    entry = _entry(lambda: _command(_compiled(), asked))

    # When `wio context k3m9xq deliver architecture` runs
    code, out, err = run_main(_ARGV, [entry])

    # Then the output is the text, each warning is a line, and it exits 0
    assert (code, out) == (0, "the bundle\n\n")
    assert err.splitlines() == [
        "warning: zulu thing",
        "warning: alpha thing",
        "warning: zulu thing",
    ]
    assert asked == [("k3m9xq", "deliver", "architecture")]


def test_there_is_no_json_option() -> None:
    """The command prints raw text for a session, so it declares no `--json`."""
    # Given a command over a fake compiler that records what it is asked
    asked: list[tuple[str, str, str]] = []
    entry = _entry(lambda: _command(_compiled(), asked))

    # When `wio context` runs with `--json`
    code, out, _ = run_main([*_ARGV, "--json"], [entry])

    # Then it is a usage error, and nothing was compiled or printed
    assert (code, out, asked) == (2, "", [])


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


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        (["--output", "chosen.md"], "chosen.md"),
        (["--output"], None),
        (["--output=old.md", "--output"], None),
    ],
)
def test_file_output_reaches_delivery_with_the_compiled_bundle(
    monkeypatch: pytest.MonkeyPatch,
    options: list[str],
    expected: str | None,
) -> None:
    """The command hands file delivery the bundle and prints its answer."""
    # Given a fixed delivery boundary and a compiled bundle
    calls: list[tuple[CompiledBundle, str | None, object, object, object]] = []

    def deliver(
        bundle: CompiledBundle,
        path: str | None,
        _repository: object,
        _files: object,
        _directories: object,
    ) -> tuple[str, tuple[str, ...]]:
        """Record the request and return a displayed path and warning.

        Args:
            bundle: The bundle to deliver.
            path: The requested path.
            _repository: The repository port.
            _files: The filesystem port.
            _directories: The directories port.

        Returns:
            The displayed path and one warning.
        """
        calls.append((bundle, path, _repository, _files, _directories))
        return "chosen.md", ("inside worktree",)

    monkeypatch.setattr("wio.context.delivery.write_bundle", deliver)
    command = _command(_compiled())
    entry = _entry(lambda: command)

    # When file output is requested
    code, out, err = run_main([*_ARGV, *options], [entry])

    # Then the boundary receives the bundle and its output is reported
    assert (code, out) == (0, "chosen.md\n")
    assert len(calls) == 1
    bundle, path, repository, files, directories = calls[0]
    assert (bundle, path) == (_compiled().bundle, expected)
    assert repository is command.services.repository
    assert files is command.services.files
    assert directories is command.services.directories
    assert err.endswith("warning: inside worktree\n")


class _PartialWriteFiles(MemoryFileSystem):
    """A filesystem whose bundle write fails after writing a prefix."""

    @override
    def write_text(self, path: Path, text: str) -> None:
        """Write a prefix, then simulate a filesystem failure.

        Args:
            path: The destination.
            text: The bundle text.

        Raises:
            OSError: After a partial write.
        """
        super().write_text(path, text[:3])
        message = "write failed"
        raise OSError(28, message)


@pytest.mark.parametrize("options", [["--output"], ["--output", "out.md"]])
def test_partial_write_failure_is_reported_without_bundle_output(
    options: list[str],
) -> None:
    """AC-5: a file-write error is reported even after writing starts."""
    # Given a compiler and a filesystem whose write fails after a prefix
    services = Services(
        FakeRepository(),
        _PartialWriteFiles(),
        FakeEnvironment(ROOT),
        FakeDirectories(ROOT),
        SettingsStub(Config()),
        EventSinkFake(),
        ReviewedCommitFake(),
    )
    command = ContextCommand(services, lambda *_args: _compiled())
    entry = _entry(lambda: command)

    # When a default or named bundle file is requested
    code, out, err = run_main([*_ARGV, *options], [entry])

    # Then the error names the destination, gives applicable hints, and prints no bundle
    assert (code, out) == (2, "")
    if len(options) == 1:
        assert "4f3a9c01b2d7.md" in err
        assert "$TMPDIR" in err
        assert "--output <path>" in err
    else:
        assert "out.md" in err
        assert "$TMPDIR" not in err
        assert "--output <path>" not in err


def test_the_size_boundary_receives_the_compiled_size_and_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The command reports the size boundary's warning before delivery."""
    # Given a size boundary that records its inputs and a failed delivery
    calls: list[tuple[int, int | None]] = []

    def warn(size: int, threshold: int | None) -> str | None:
        """Record the inputs and give a warning.

        Args:
            size: The compiler's body size.
            threshold: The configured threshold.

        Returns:
            A fixed warning.
        """
        calls.append((size, threshold))
        return "fixed size warning"

    monkeypatch.setattr("wio.context.size_warning.size_warning", warn)
    services = Services(
        FakeRepository(),
        _PartialWriteFiles(),
        FakeEnvironment(ROOT),
        FakeDirectories(ROOT),
        SettingsStub(Config(bundle=Bundle(size_threshold=9))),
        EventSinkFake(),
        ReviewedCommitFake(),
    )
    command = ContextCommand(services, lambda *_args: _compiled())

    # When file delivery fails after compilation
    code, out, err = run_main([*_ARGV, "--output", "out.md"], [_entry(lambda: command)])

    # Then the compiled body size and configured threshold were judged first
    assert calls == [(12, 9)]
    assert (code, out) == (2, "")
    assert "warning: fixed size warning\n" in err
    assert err.index("warning: fixed size warning") < err.index("error:")
