# SPDX-License-Identifier: Apache-2.0
"""Tests of the test drivers against the real command and the real process."""

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.drivers.base import RunResult
from tests.acceptance.drivers.cli import CliDriver
from tests.acceptance.drivers.in_process import InProcessDriver
from tests.sandbox import Sandbox

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.io.ports import Stdio


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


def test_the_in_process_driver_runs_in_the_sandbox(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The call sees the sandbox's directory and environment, then restores."""
    # Given the in-process driver and a main that records its surroundings
    seen: list[tuple[Path, dict[str, str]]] = []

    def record(argv: Sequence[str], stdio: Stdio) -> int:
        """Remember the working directory and the environment.

        Args:
            argv: The arguments, ignored.
            stdio: The streams, ignored.

        Returns:
            Exit code 0.
        """
        del argv, stdio
        seen.append((Path.cwd(), dict(os.environ)))
        return 0

    monkeypatch.setattr("wio.cli.main", record)
    before = (Path.cwd(), dict(os.environ))

    # When it runs wio
    InProcessDriver(sandbox).run([])

    # Then the call saw the sandbox's, and the process has its own again
    after = (Path.cwd(), dict(os.environ))
    assert seen == [(sandbox.root.resolve(), sandbox.env)]
    assert after == before
