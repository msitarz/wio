# SPDX-License-Identifier: Apache-2.0
"""Tests for the facade and the test drivers of the acceptance setup."""

import subprocess
from typing import TYPE_CHECKING, Any

from tests.acceptance.drivers.base import RunResult
from tests.acceptance.drivers.cli import SCRIPT, CliDriver
from tests.acceptance.dsl.results import Output
from tests.acceptance.dsl.wio import Wio

if TYPE_CHECKING:
    from collections.abc import Sequence

    import pytest

    from tests.sandbox import Sandbox


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


def test_the_cli_driver_runs_in_the_sandbox(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The subprocess gets the sandbox's directory and environment."""
    # Given the CLI driver and a spy in place of subprocess.run
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
