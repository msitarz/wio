# SPDX-License-Identifier: Apache-2.0
"""The real adapters of the ports of `wio.io`."""

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import TextIO


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
        """
        return path.read_bytes().decode("utf-8")

    def read_bytes(self, path: Path) -> bytes:
        """Read a file as it is stored.

        Args:
            path: The file to read.

        Returns:
            The file's bytes.
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
            The entries sorted by name.
        """
        return sorted(path.iterdir(), key=lambda entry: entry.name)


def _git_path(*arguments: str) -> Path:
    """Run `git rev-parse` in the working directory and read the path it prints.

    Args:
        *arguments: The options after `git rev-parse`.

    Returns:
        The path git printed.

    Raises:
        RuntimeError: If the working directory is not inside a repository, or
            git is not installed.
    """
    try:
        done = subprocess.run(
            ["git", "rev-parse", *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as error:
        message = f"cannot run git: {error}"
        raise RuntimeError(message) from error
    if done.returncode != 0:
        message = f"not inside a git repository: {done.stderr.strip()}"
        raise RuntimeError(message)
    return Path(done.stdout.strip())


class GitRepository:
    """The repository of the working directory, read with git, as `Repository`.

    `root` and `identity` ask git. `show_index` and `is_dirty` belong to the
    trailers Work and raise `NotImplementedError` until it implements them.
    """

    def root(self) -> Path:
        """Find the top of the working tree.

        Returns:
            The absolute path of the repository root.
        """
        return _git_path("--show-toplevel")

    def identity(self) -> Path:
        """Find the path that identifies the clone.

        Returns:
            The absolute path of the git directory that every worktree of one
            clone shares.
        """
        return _git_path("--path-format=absolute", "--git-common-dir")

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
