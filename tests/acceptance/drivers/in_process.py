# SPDX-License-Identifier: Apache-2.0
"""The in-process test driver: calls `wio.cli.main` with in-memory streams."""

import contextlib
import io
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, TextIO
from unittest import mock

from tests.acceptance.drivers.base import RunResult, SandboxedDriver
from wio import cli

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass
class MemoryStdio:
    """In-memory standard streams that satisfy the `Stdio` port."""

    stdin: TextIO
    stdout: TextIO
    stderr: TextIO


class InProcessDriver(SandboxedDriver):
    """Reaches `wio` by calling its testable core in this process.

    The working directory and the home and data variables are the sandbox's
    while the call runs, and are restored afterwards.
    """

    def run(self, args: Sequence[str]) -> RunResult:
        """Call `wio.cli.main` inside the sandbox.

        Args:
            args: The arguments after the program name.

        Returns:
            The text the call wrote to its streams and its exit code.
        """
        out, err = io.StringIO(), io.StringIO()
        stdio = MemoryStdio(io.StringIO(), out, err)
        env = self._sandbox.env
        private = {key: env[key] for key in ("HOME", "XDG_DATA_HOME")}
        with (
            contextlib.chdir(self._sandbox.root),
            mock.patch.dict(os.environ, private),
        ):
            code = cli.main(list(args), stdio)
        return RunResult(out.getvalue(), err.getvalue(), code)
