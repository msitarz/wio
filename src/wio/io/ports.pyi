# SPDX-License-Identifier: Apache-2.0
"""The ports of `wio.io`: how wio reaches the world outside the process.

These ports are shared infrastructure that `wio.io` owns, an exception to the
rule that the consumer owns its ports. A component reaches the filesystem,
standard streams, git and the environment only through them. Provisional: the
members of `FileSystem`, `Git` and `Environment` are the ones the scope
document needs, and the architecture review may rename them; `Stdio` is
required as written.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, TextIO

class FileSystem(Protocol):
    """Reads and writes text files and lists directories.

    Paths are absolute or relative to the working directory, and a failure
    raises the `OSError` subclass that describes it.
    """

    def read_text(self, path: Path) -> str:
        """Read a file as UTF-8 text.

        Args:
            path: The file to read.

        Returns:
            The file's content, with its line ends as stored.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        ...

    def write_text(self, path: Path, text: str) -> None:
        """Write a file as UTF-8 text, creating its parent directories.

        Args:
            path: The file to write.
            text: The content, written exactly as given.
        """
        ...

    def exists(self, path: Path) -> bool:
        """Tell whether a path exists.

        Args:
            path: A file or directory.

        Returns:
            True when the path exists.
        """
        ...

    def list_dir(self, path: Path) -> Sequence[Path]:
        """List a directory's entries.

        Args:
            path: The directory.

        Returns:
            The entries sorted by name, so output never depends on the
            filesystem's order.

        Raises:
            NotADirectoryError: If the path is not a directory.
        """
        ...

class Stdio(Protocol):
    """The three standard streams of one run of wio.

    A command reads and writes only through these, never through `sys`, so a
    test can give it in-memory streams.
    """

    stdin: TextIO
    """The stream a command reads input from."""

    stdout: TextIO
    """The stream a command writes its results to."""

    stderr: TextIO
    """The stream a command writes notes, warnings and errors to."""

class Git(Protocol):
    """Reads a git repository's history and file contents."""

    def rev_parse(self, revision: str) -> str:
        """Resolve a revision to a full commit id.

        Args:
            revision: A revision such as `HEAD`.

        Returns:
            The full commit id.

        Raises:
            ValueError: If the revision does not name a commit.
        """
        ...

    def messages(self, revision_range: str) -> Sequence[str]:
        """List the commit messages of a revision range.

        Args:
            revision_range: A range such as `main..HEAD`.

        Returns:
            The messages, oldest first.
        """
        ...

    def show(self, revision: str, path: Path) -> str | None:
        """Read a file as it was at a revision.

        Args:
            revision: The revision, such as `HEAD`.
            path: The file, relative to the repository root.

        Returns:
            The file's content, or `None` when it did not exist then.
        """
        ...

class Environment(Protocol):
    """Reads the process environment and the working directory."""

    def get(self, name: str) -> str | None:
        """Read an environment variable.

        Args:
            name: The variable's name.

        Returns:
            Its value, or `None` when it is not set.
        """
        ...

    def working_directory(self) -> Path:
        """Find the directory the command runs in.

        Returns:
            The absolute working directory.
        """
        ...
