# SPDX-License-Identifier: Apache-2.0
"""The ports of `wio.io`: how wio reaches the world outside the process.

These ports are shared infrastructure that `wio.io` owns, an exception to the
rule that the consumer owns its ports. A component reaches the filesystem,
standard streams and the repository only through them, and no port names a
tool. Provisional: the members of `FileSystem`, `Repository` and `History` are
the ones the data flows of the scope document need, and the Works that add an
adapter may rename or extend them; `Stdio` is required as written.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, TextIO

from wio.models.commits import Commit

class FileSystem(Protocol):
    """Reads and writes files and lists directories.

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
        ...

    def read_bytes(self, path: Path) -> bytes:
        """Read a file as it is stored, for hashing.

        Args:
            path: The file to read.

        Returns:
            The file's bytes.

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

    def append_text(self, path: Path, text: str) -> None:
        """Append UTF-8 text to a file in one write, creating it if needed.

        The text reaches the file in a single append, so writers that run at
        the same time do not interleave their lines.

        Args:
            path: The file to append to, whose parents are created.
            text: The content, appended exactly as given.
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

    def is_dir(self, path: Path) -> bool:
        """Tell whether a path is a directory.

        Args:
            path: Any path.

        Returns:
            True when the path exists and is a directory.
        """
        ...

    def is_file(self, path: Path) -> bool:
        """Tell whether a path is a regular file.

        Args:
            path: Any path.

        Returns:
            True when the path exists and is a regular file.
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

class Repository(Protocol):
    """Tells where the repository is and what state its index and changes are in.

    Every method raises `RuntimeError` when the working directory is not inside
    a repository.
    """

    def root(self) -> Path:
        """Find the top of the working tree.

        Returns:
            The absolute path of the repository root, the base of every path
            that `History.show` and `History.list_files` take.
        """
        ...

    def identity(self) -> Path:
        """Find the path that identifies the clone.

        Returns:
            The absolute path that every checkout of one clone shares, so
            worktrees of one clone have the same identity.
        """
        ...

    def show_index(self, path: Path) -> str | None:
        """Read a file as it is staged in the index.

        Args:
            path: The file, relative to the repository root.

        Returns:
            The staged content, or `None` when the index has no such file.
        """
        ...

    def is_dirty(self) -> bool:
        """Tell whether the working tree has uncommitted changes.

        Returns:
            True when a tracked file differs from `HEAD` or the index, or when
            an untracked file that is not ignored exists.
        """
        ...

class History(Protocol):
    """Reads the revisions of a repository, and never changes them.

    Every method raises `RuntimeError` when the working directory is not inside
    a repository, and `ValueError` for a revision or range that is rejected.
    """

    def rev_parse(self, revision: str) -> str:
        """Resolve a revision to a full commit id.

        Args:
            revision: A revision such as `HEAD`.

        Returns:
            The full commit id.
        """
        ...

    def history(self, revision_range: str) -> Sequence[Commit]:
        """List the commits of a revision range.

        Args:
            revision_range: A range such as `main..HEAD`.

        Returns:
            The commits oldest first, parents before children.
        """
        ...

    def first_parents(self, revision: str) -> Sequence[Commit]:
        """List a revision's ancestors along first parents.

        Args:
            revision: The revision to start from, such as `HEAD`.

        Returns:
            The commits newest first, starting with the revision's own.
        """
        ...

    def list_files(self, revision: str) -> Sequence[Path]:
        """List the files of a revision's tree.

        Args:
            revision: The revision, such as `HEAD`.

        Returns:
            The paths relative to the repository root, sorted.
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
