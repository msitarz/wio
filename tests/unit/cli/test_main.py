# SPDX-License-Identifier: Apache-2.0
"""Tests for the composition root of the `wio` command."""

import importlib.metadata
import io
from dataclasses import dataclass
from typing import TYPE_CHECKING, TextIO

from wio import cli

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pytest

    from wio.io.ports import Stdio


@dataclass
class FakeStdio:
    """In-memory standard streams that satisfy the `Stdio` port."""

    stdin: TextIO
    stdout: TextIO
    stderr: TextIO


def test_console_main_runs_the_core_on_the_real_streams(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The console function shows the summary on the process's own streams."""
    # Given the process arguments of a bare `wio`
    monkeypatch.setattr("sys.argv", ["wio"])

    # When the console function runs
    code = cli.console_main()

    # Then it returns 0 and prints the usage with the summary
    captured = capsys.readouterr()
    assert code == 0
    assert captured.out.startswith("usage: wio")
    assert importlib.metadata.metadata("work-it-out")["Summary"] in captured.out
    assert captured.err == ""


def test_console_main_runs_the_core_on_the_adapter_for_the_process_streams(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The console function builds the stream adapter and hands it to `main`."""
    # Given a stream adapter that is a fake, and a core that records its call
    out = io.StringIO()
    fake = FakeStdio(io.StringIO(), out, io.StringIO())
    calls: list[tuple[list[str], object]] = []

    def record(argv: Sequence[str], stdio: Stdio) -> int:
        """Remember the call and answer 7.

        Args:
            argv: The arguments the core received.
            stdio: The streams the core received.

        Returns:
            The fixed exit code 7.
        """
        calls.append((list(argv), stdio))
        return 7

    monkeypatch.setattr("sys.argv", ["wio", "x", "y"])
    monkeypatch.setattr("wio.io.adapters.SystemStdio", lambda: fake)
    monkeypatch.setattr(cli, "main", record)

    # When the console function runs
    code = cli.console_main()

    # Then it passed the arguments after the program name and the fake streams
    assert calls == [(["x", "y"], fake)]
    assert code == 7
