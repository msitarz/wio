# SPDX-License-Identifier: Apache-2.0
"""The in-process test driver: calls `wio.cli.main` with in-memory streams."""

import contextlib
import io
import os
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Protocol, TextIO
from unittest import mock

from tests.acceptance.drivers.base import RunResult, SandboxedDriver
from wio import cli
from wio.context import Compiled
from wio.models.bundle import CompiledBundle

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
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
    needs no history runs without starting a process. It supplies a synthetic
    clone identity for standalone repositories. Scenarios that need real git
    discovery, shared worktrees, the index or history run on the CLI channel.

    Attributes:
        environment: Reports the working directory.
        top: The root to answer with, or `None` for the working directory, which
            a run that starts below the root of the sandbox gives.
    """

    environment: _Directory
    top: Path | None = None

    def root(self) -> Path:
        """Find the top of the working tree.

        Returns:
            The root the repository was given, or else the absolute working
            directory.
        """
        return self.top or self.environment.working_directory()

    def identity(self) -> Path:
        """Identify the standalone clone of the scenario.

        Returns:
            A synthetic git common directory under the sandbox root.
        """
        return self.root().resolve() / ".git"

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

    def run(
        self, args: Sequence[str], directory: str | None = None, stdin: str = ""
    ) -> RunResult:
        """Call `wio.cli.main` inside the sandbox.

        Args:
            args: The arguments after the program name.
            directory: A directory below the sandbox's root to run in, or `None`.
                The repository's root is the sandbox's either way.
            stdin: What standard input holds.

        Returns:
            The text the call wrote to its streams and its exit code.
        """
        out, err = io.StringIO(), io.StringIO()
        stdio = MemoryStdio(io.StringIO(stdin), out, err)
        root = self._sandbox.root
        with (
            contextlib.chdir(self._directory(directory)),
            mock.patch.dict(os.environ, self._sandbox.env, clear=True),
            mock.patch(
                "wio.io.adapters.GitRepository", partial(SandboxRepository, top=root)
            ),
        ):
            code = cli.main(list(args), stdio)
        return RunResult(out.getvalue(), err.getvalue(), code)

    def git(self, args: Sequence[str]) -> RunResult:
        """Refuse: the sandbox of this channel is not a git repository.

        Args:
            args: The arguments after `git`, ignored.

        Raises:
            NotImplementedError: Always; run the scenario on the CLI channel.
        """
        raise NotImplementedError(str(args))


@contextlib.contextmanager
def fixed_composition(text: str) -> Iterator[None]:
    """Replace bundle composition while keeping the command's checks real.

    Args:
        text: The bundle text the composition returns.

    Yields:
        Control while the fixed composition is installed.
    """
    bundle = CompiledBundle(text=text, id="fixed", size=0, rules={})
    with mock.patch("wio.context.Composition.compose", return_value=bundle):
        yield


@contextlib.contextmanager
def unavailable_temporary_directory() -> Iterator[None]:
    """Make the system temporary directory unavailable to the command.

    Yields:
        Control while temporary-directory discovery fails.
    """
    with mock.patch(
        "wio.env.adapters.ProcessDirectories.temp_dir",
        side_effect=OSError("unavailable"),
    ):
        yield


@contextlib.contextmanager
def fixed_compiler(text: str, size: int) -> Iterator[None]:
    """Supply a fixed compiler result to the command in this channel.

    Args:
        text: The bundle delivered by the command.
        size: The body size reported by the compiler.

    Yields:
        Control while the compiler returns the fixed result.
    """
    bundle = CompiledBundle(text=text, id="fixed", size=size, rules={})
    with mock.patch("wio.context.Compiler.compile", return_value=Compiled(bundle, ())):
        yield
