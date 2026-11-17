# SPDX-License-Identifier: Apache-2.0
"""The test driver Protocol: how a scenario's facade reaches `wio`."""

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from tests.sandbox import Sandbox

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
"""The static sample repositories a scenario can install, one directory each."""


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

    def run(
        self, args: Sequence[str], directory: str | None = None, stdin: str = ""
    ) -> RunResult:
        """Run `wio` with the given arguments in the driver's sandbox.

        Args:
            args: The arguments after the program name.
            directory: A directory below the root of the sandbox to run in, or
                `None` to run at the root. The repository stays the sandbox.
            stdin: What standard input holds.

        Returns:
            The streams and exit code of the run.
        """
        ...

    def git(self, args: Sequence[str]) -> RunResult:
        """Run git with the given arguments in the root of the sandbox.

        Only a channel that has a real repository implements it; the committer is
        the fixed identity of the sandbox.

        Args:
            args: The arguments after `git`.

        Returns:
            The streams and exit code of the run.
        """
        ...

    def install(self, fixture: str) -> None:
        """Put a static sample repository in the driver's sandbox.

        Args:
            fixture: The path of the fixture under `tests/fixtures`, such as
                `config/rich`; its files are copied to the root of the sandbox.
        """
        ...

    def put(self, path: str, data: bytes) -> None:
        """Write a file into the driver's sandbox, with its directories.

        Args:
            path: The file, relative to the root of the sandbox.
            data: Its bytes.
        """
        ...

    def read(self, path: str) -> bytes:
        """Read a file of the scenario's repository.

        Args:
            path: The file relative to the root.

        Returns:
            The file's bytes.
        """
        ...

    def fingerprint(self, directory: str) -> dict[str, str]:
        """Fingerprint every file below a directory of the sandbox.

        Args:
            directory: The directory, relative to the root of the sandbox.

        Returns:
            The SHA-256 of each file by its path relative to the directory,
            written with `/`.
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

    def _directory(self, directory: str | None) -> Path:
        """Find the directory a run starts in.

        Args:
            directory: A directory below the root of the sandbox, or `None`.

        Returns:
            That directory, or the root of the sandbox for `None`.
        """
        root = self._sandbox.root
        return root if directory is None else root / directory

    def install(self, fixture: str) -> None:
        """Copy a fixture to the root of the sandbox.

        Args:
            fixture: The path of the fixture under `tests/fixtures`.
        """
        shutil.copytree(FIXTURES / fixture, self._sandbox.root, dirs_exist_ok=True)

    def put(self, path: str, data: bytes) -> None:
        """Create the file below the root of the sandbox, and its directories.

        Args:
            path: Where the file goes, relative to that root.
            data: What it holds.
        """
        target = self._sandbox.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def read(self, path: str) -> bytes:
        """Read a repository file as bytes.

        Args:
            path: The file relative to the root.

        Returns:
            The file's bytes.
        """
        return (self._sandbox.root / path).read_bytes()

    def fingerprint(self, directory: str) -> dict[str, str]:
        """Hash every file found below a directory of the sandbox.

        Args:
            directory: The directory to walk, relative to the root.

        Returns:
            Each file's SHA-256 under its path relative to the directory.
        """
        base = self._sandbox.root / directory
        return {
            path.relative_to(base).as_posix(): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(base.rglob("*"))
            if path.is_file()
        }
