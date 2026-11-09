# SPDX-License-Identifier: Apache-2.0
"""The CLI test driver: runs the installed `wio` command in a subprocess."""

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, override

from tests.acceptance.drivers.base import RunResult, SandboxedDriver

if TYPE_CHECKING:
    from collections.abc import Sequence

SCRIPT = Path(sys.executable).parent / "wio"


class CliDriver(SandboxedDriver):
    """Reaches `wio` through its console script, as a user does.

    The script is found next to the Python executable of the environment, so no
    shell is involved.
    """

    def run(self, args: Sequence[str]) -> RunResult:
        """Run the command in the sandbox's directory and environment.

        Args:
            args: The arguments after the program name.

        Returns:
            The decoded streams and the exit code of the process.
        """
        done = subprocess.run(
            [str(SCRIPT), *args],
            cwd=self._sandbox.root,
            env=self._sandbox.env,
            capture_output=True,
            text=True,
            check=False,
        )
        return RunResult(done.stdout, done.stderr, done.returncode)

    @override
    def install(self, fixture: str) -> None:
        """Copy a fixture and make the sandbox a git repository, as a user has.

        Args:
            fixture: The path of the fixture under `tests/fixtures`.
        """
        super().install(fixture)
        subprocess.run(
            ["git", "init", "--quiet"],
            cwd=self._sandbox.root,
            env=self._sandbox.env,
            check=True,
        )
