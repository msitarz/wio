# SPDX-License-Identifier: Apache-2.0
"""The test driver Protocol: how a scenario's facade reaches `wio`."""

import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from tests.sandbox import Sandbox


@dataclass(frozen=True)
class RunResult:
    """What one run of `wio` produced, as plain data.

    Attributes:
        stdout: Everything written to standard output.
        stderr: Everything written to standard error.
        exit_code: The exit code of the run.
    """

    stdout: str
    stderr: str
    exit_code: int


class WioDriver(Protocol):
    """A test driver: runs `wio` on one channel and returns data.

    An implementation never asserts, so every channel gives a scenario the same
    kind of value.
    """

    def run(self, args: Sequence[str]) -> RunResult:
        """Run `wio` with the given arguments in the driver's sandbox.

        Args:
            args: The arguments after the program name.

        Returns:
            The streams and exit code of the run.
        """
        ...

    def prepare(self, files: Mapping[str, str]) -> None:
        """Make the driver's sandbox a git repository that holds some files.

        Args:
            files: The text of each file by its path relative to the root of the
                repository; its directories are created.
        """
        ...


class SandboxedDriver:
    """The part of a test driver that holds its sandbox.

    A subclass implements `run` and reads the directory and environment from
    the sandbox it was built from.
    """

    def __init__(self, sandbox: Sandbox) -> None:
        """Remember the sandbox the driver runs `wio` in.

        Args:
            sandbox: The directory and environment to give `wio`.
        """
        self._sandbox = sandbox

    def prepare(self, files: Mapping[str, str]) -> None:
        """Initialize a git repository in the sandbox and write the files.

        Args:
            files: The text of each file by its path relative to the root of the
                repository; its directories are created.
        """
        subprocess.run(
            ["git", "init", "--quiet"],
            cwd=self._sandbox.root,
            env=self._sandbox.env,
            check=True,
        )
        for name, text in files.items():
            path = self._sandbox.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
