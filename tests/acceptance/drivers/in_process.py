# SPDX-License-Identifier: Apache-2.0
"""The in-process test driver: calls `wio.cli.main` with in-memory streams."""

import contextlib
import io
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, TextIO
from unittest import mock

from tests.acceptance.drivers.base import RunResult, SandboxedDriver
from wio import cli

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


class _Directory(Protocol):
    """What `SandboxRepository` needs of the environment it is given."""

    def working_directory(self) -> Path:
        """Find the directory the command runs in.

        Returns:
            The absolute working directory.
        """
        ...


@dataclass(frozen=True)
class SandboxRepository:
    """A `Repository` whose root is the working directory, with no git behind it.

    The in-process channel swaps it in for the git adapter, so a scenario that
    needs no history runs without starting a process. It answers `root` only: a
    scenario that tells clones apart, or reads the index or the history, runs on
    the CLI channel, against real git.

    Attributes:
        environment: Reports the working directory.
    """

    environment: _Directory

    def root(self) -> Path:
        """Find the top of the working tree: the working directory itself.

        Returns:
            The absolute working directory.
        """
        return self.environment.working_directory()

    def identity(self) -> Path:
        """Refuse: no scenario of this channel tells clones apart.

        Raises:
            NotImplementedError: Always; run the scenario on the CLI channel.
        """
        raise NotImplementedError

    def show_index(self, path: Path) -> str | None:
        """Refuse: no scenario of this channel reads the index.

        Args:
            path: The file, ignored.

        Raises:
            NotImplementedError: Always; run the scenario on the CLI channel.
        """
        raise NotImplementedError(str(path))

    def is_dirty(self) -> bool:
        """Refuse: no scenario of this channel reads the state of the tree.

        Raises:
            NotImplementedError: Always; run the scenario on the CLI channel.
        """
        raise NotImplementedError


@dataclass
class MemoryStdio:
    """In-memory standard streams that satisfy the `Stdio` port."""

    stdin: TextIO
    stdout: TextIO
    stderr: TextIO


class InProcessDriver(SandboxedDriver):
    """Reaches `wio` by calling its testable core in this process.

    The working directory and the whole environment are the sandbox's while the
    call runs, and are restored afterwards. The sandbox is a plain directory: the
    git adapter is replaced by `SandboxRepository`, so no process is started.
    A scenario that needs a real repository, or none, runs on the CLI channel.
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
        with (
            contextlib.chdir(self._sandbox.root),
            mock.patch.dict(os.environ, self._sandbox.env, clear=True),
            mock.patch("wio.io.adapters.GitRepository", SandboxRepository),
        ):
            code = cli.main(list(args), stdio)
        return RunResult(out.getvalue(), err.getvalue(), code)
