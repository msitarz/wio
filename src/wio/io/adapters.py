# SPDX-License-Identifier: Apache-2.0
"""The real adapters of the ports of `wio.io`."""

import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import TextIO

    from wio.env.ports import Environment


class SystemStdio:
    """The process's own standard streams, as the `Stdio` port.

    Once built, its `stdin`, `stdout` and `stderr` are the streams of `sys`.
    """

    stdin: TextIO
    stdout: TextIO
    stderr: TextIO

    def __init__(self) -> None:
        """Bind the streams of `sys`."""
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr


class LocalFileSystem:
    """The local disk, as the `FileSystem` port.

    Paths are absolute or relative to the working directory, and a failure to
    reach a file raises the `OSError` subclass that describes it.
    """

    def read_text(self, path: Path) -> str:
        """Read a file as UTF-8 text.

        Args:
            path: The file to read.

        Returns:
            The file's content, with its line ends as stored.

        Raises:
            FileNotFoundError: If the file does not exist.
            UnicodeDecodeError: If the file is not valid UTF-8.
        """
        return path.read_bytes().decode("utf-8")

    def read_bytes(self, path: Path) -> bytes:
        """Read a file as it is stored.

        Args:
            path: The file to read.

        Returns:
            The file's bytes.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        return path.read_bytes()

    def write_text(self, path: Path, text: str) -> None:
        """Write a file as UTF-8 text, creating its parent directories.

        Args:
            path: The file to write.
            text: The content, written exactly as given.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))

    def append_text(self, path: Path, text: str) -> None:
        """Append UTF-8 text to a file in one write, creating it if needed.

        Args:
            path: The file to append to, whose parents are created.
            text: The content, appended exactly as given.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as stream:
            stream.write(text.encode("utf-8"))

    def exists(self, path: Path) -> bool:
        """Tell whether a path exists.

        Args:
            path: A file or directory.

        Returns:
            True when the path exists.
        """
        return path.exists()

    def is_dir(self, path: Path) -> bool:
        """Tell whether a path is a directory.

        Args:
            path: Any path.

        Returns:
            True when the path exists and is a directory.
        """
        return path.is_dir()

    def is_file(self, path: Path) -> bool:
        """Tell whether a path is a regular file.

        Args:
            path: Any path.

        Returns:
            True when the path exists and is a regular file.
        """
        return path.is_file()

    def list_dir(self, path: Path) -> Sequence[Path]:
        """List a directory's entries.

        Args:
            path: The directory.

        Returns:
            The entries sorted by name, so the listing never depends on the
            order the disk returns.

        Raises:
            FileNotFoundError: If the path does not exist.
            NotADirectoryError: If the path is not a directory.
        """
        return sorted(path.iterdir(), key=lambda entry: entry.name)


_NEXT = "run wio from a directory inside the repository"


def _check_directory(directory: Path) -> None:
    """Check that the directory git is to run in exists and can be entered.

    Args:
        directory: The working directory the environment reported.

    Raises:
        RuntimeError: If it does not exist, is not a directory or cannot be
            entered. The message names it, says which, and says to run wio
            from inside the repository.
    """
    if not directory.exists():
        message = f"the working directory {directory} does not exist; {_NEXT}"
        raise RuntimeError(message)
    if not directory.is_dir():
        message = f"the working directory {directory} is not a directory; {_NEXT}"
        raise RuntimeError(message)
    if not os.access(directory, os.X_OK):
        message = f"the working directory {directory} cannot be entered; {_NEXT}"
        raise RuntimeError(message)


def _git_path(environment: Environment, *arguments: str) -> Path:
    """Run `git rev-parse` in the environment's directory and read its path.

    Args:
        environment: Reports the working directory git runs in.
        *arguments: The options after `git rev-parse`.

    Returns:
        The path git printed.

    Raises:
        RuntimeError: If the working directory does not exist, is not a
            directory or is not inside a repository, or git cannot be run. Each
            message says what is wrong and what to do, and names the working
            directory the environment reported, except when git cannot be run.
    """
    directory = environment.working_directory()
    _check_directory(directory)
    try:
        done = subprocess.run(
            ["git", "rev-parse", *arguments],
            cwd=directory,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        reason = error.strerror or str(error)
        message = f"cannot run git: {reason}; check that git is installed and on PATH"
        raise RuntimeError(message) from error
    if done.returncode != 0:
        message = (
            f"not inside a git repository (working directory {directory}); {_NEXT}"
        )
        raise RuntimeError(message)
    return Path(done.stdout.strip())


class GitRepository:
    """The repository of the working directory, read with git, as `Repository`.

    `root` and `identity` ask git, which must be installed wherever wio runs
    because the `git` trailer reader needs it too. A missing git, a working
    directory that does not exist, is not a directory or cannot be entered, and
    a directory outside a repository each raise a `RuntimeError` that says which
    and what to do, and names the working directory except when git cannot be
    run. `show_index` and `is_dirty` belong to the trailers Work: they exist and
    raise `NotImplementedError` so that the class has every member of
    `Repository` and can be wired where the port is expected, until that Work
    gives them their meaning.

    It is given an `Environment` and runs git in the working directory that the
    environment reports, never in one it finds itself, so a test can fix it.
    """

    def __init__(self, environment: Environment) -> None:
        """Keep the environment that tells where the working directory is.

        Args:
            environment: Reports the working directory git runs in.
        """
        self._environment: Environment = environment

    def root(self) -> Path:
        """Find the top of the working tree.

        Returns:
            The absolute path of the repository root.
        """
        return _git_path(self._environment, "--show-toplevel")

    def identity(self) -> Path:
        """Find the path that identifies the clone.

        Returns:
            The absolute path of the git directory that every worktree of one
            clone shares.
        """
        return _git_path(
            self._environment, "--path-format=absolute", "--git-common-dir"
        )

    def show_index(self, path: Path) -> str | None:
        """Read a file as it is staged in the index.

        Args:
            path: The file, relative to the repository root.

        Raises:
            NotImplementedError: Always, until the trailers Work implements it.
        """
        message = f"show_index({path}) is implemented by the trailers Work"
        raise NotImplementedError(message)

    def is_dirty(self) -> bool:
        """Tell whether the working tree has uncommitted changes.

        Raises:
            NotImplementedError: Always, until the trailers Work implements it.
        """
        message = "is_dirty is implemented by the trailers Work"
        raise NotImplementedError(message)
