# SPDX-License-Identifier: Apache-2.0
"""Tests for the facade and the test drivers of the acceptance setup."""

import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from tests.acceptance.drivers.base import RunResult
from tests.acceptance.drivers.cli import SCRIPT, CliDriver
from tests.acceptance.drivers.in_process import InProcessDriver
from tests.acceptance.dsl.results import Output
from tests.acceptance.dsl.wio import Wio
from tests.acceptance.sandbox import Sandbox

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.io.ports import Stdio


class FakeDriver:
    """A test driver that returns a fixed result."""

    def run(self, args: Sequence[str]) -> RunResult:
        """Answer with a fixed result whatever the arguments.

        Args:
            args: The arguments, ignored.

        Returns:
            The fixed result.
        """
        del args
        return RunResult("usage\n", "warning\n", 3)


def test_the_facade_maps_a_result_to_an_output() -> None:
    """`bare()` turns the driver's result into both streams and an exit code."""
    # Given a fake test driver that returns a result
    wio = Wio(FakeDriver())

    # When wio is run bare through the facade
    output = wio.bare()

    # Then the output carries both streams and the exit code
    assert output == Output(stdout="usage\n", stderr="warning\n", exit_code=3)


@pytest.mark.slow
def test_both_test_drivers_return_the_same_data(tmp_path: Path) -> None:
    """The in-process and the CLI driver agree on a bare run."""
    # Given both test drivers, each on its own empty prepared repository
    in_process = InProcessDriver(Sandbox.under(tmp_path / "a"))
    cli = CliDriver(Sandbox.under(tmp_path / "b"))

    # When each runs wio with no arguments
    first = in_process.run([])
    second = cli.run([])

    # Then each returns a result, and the two are equal
    assert isinstance(first, RunResult)
    assert first == second


def test_the_cli_driver_runs_in_the_sandbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The subprocess gets the sandbox's directory and environment."""
    # Given the CLI driver and a spy in place of subprocess.run
    sandbox = Sandbox.under(tmp_path)
    calls: list[dict[str, Any]] = []

    def spy(
        command: list[str],
        **kwargs: Any,  # noqa: ANN401
    ) -> subprocess.CompletedProcess[str]:
        """Record the call and answer with a silent success.

        Args:
            command: The command line.
            **kwargs: The options of the call.

        Returns:
            A completed process with no output.
        """
        calls.append({"command": command, **kwargs})
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", spy)

    # When it runs wio
    CliDriver(sandbox).run(["x"])

    # Then the spy received the command, the sandbox's root and its environment
    assert calls[0]["command"] == [str(SCRIPT), "x"]
    assert calls[0]["cwd"] == sandbox.root
    assert calls[0]["env"] == sandbox.env


def test_the_in_process_driver_runs_in_the_sandbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The call sees the sandbox's directory and variables, then restores."""
    # Given the in-process driver and a main that records its surroundings
    sandbox = Sandbox.under(tmp_path)
    seen: list[tuple[Path, str | None, str | None]] = []

    def record(argv: Sequence[str], stdio: Stdio) -> int:
        """Remember the working directory and the two variables.

        Args:
            argv: The arguments, ignored.
            stdio: The streams, ignored.

        Returns:
            Exit code 0.
        """
        del argv, stdio
        seen.append(
            (
                Path.cwd(),
                os.environ.get("HOME"),
                os.environ.get("XDG_DATA_HOME"),
            )
        )
        return 0

    monkeypatch.setattr("wio.cli.main", record)
    before = (Path.cwd(), os.environ.get("HOME"), os.environ.get("XDG_DATA_HOME"))

    # When it runs wio
    InProcessDriver(sandbox).run([])

    # Then the call saw the sandbox's, and the process has its own again
    after = (Path.cwd(), os.environ.get("HOME"), os.environ.get("XDG_DATA_HOME"))
    assert seen == [
        (
            sandbox.root.resolve(),
            sandbox.env["HOME"],
            sandbox.env["XDG_DATA_HOME"],
        )
    ]
    assert after == before
