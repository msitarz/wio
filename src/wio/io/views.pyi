# SPDX-License-Identifier: Apache-2.0
"""The spec of the read-only views of a repository as a `FileSystem`.

A view lets the code that reads a tree of files, such as the discovery of Works,
run unchanged on the index or on a revision instead of the working tree. A view
is an adapter of the `FileSystem` port over the `Repository` and `History`
ports, so it is imported only by `wio.cli` and the tests, and it never calls git
itself.

The stub is the spec until the wiring stage of the Work that builds the lookup
of a Work for a record writes the classes into `wio.io.views` and deletes this
stub, so the spec and the code never coexist.
"""

from collections.abc import Sequence
from pathlib import Path

from wio.io.ports import FileSystem, History, Repository

class ReadOnlyFiles:
    """What the views share: a `FileSystem` over a set of files that is read-only.

    A subclass says which files the view holds and what each contains, and this
    class answers the members of the port from that. A path is absolute, below
    the root the view was given, and a path outside it does not exist. A view
    holds files only, so a directory exists when a file lies below it, and a
    symbolic link never exists.
    """

    def __init__(self, root: Path) -> None:
        """Keep the root that the paths of the view are relative to.

        Args:
            root: The absolute path of the repository root.
        """
        ...

    def paths(self) -> frozenset[Path]:
        """List the files that the view holds.

        Returns:
            Their paths relative to the root. A subclass reads them once and
            keeps them, so every member answers from one listing.
        """
        ...

    def content(self, path: Path) -> str | None:
        """Read one file of the view.

        Args:
            path: A file that `paths` lists, relative to the root.

        Returns:
            The file's content as stored, or `None` when the view does not hold
            it.
        """
        ...

    def read_text(self, path: Path) -> str:
        """Read a file as UTF-8 text.

        Args:
            path: The file to read.

        Returns:
            The file's content, with its line ends as stored.

        Raises:
            FileNotFoundError: If the view does not hold the file.
        """
        ...

    def read_bytes(self, path: Path) -> bytes:
        """Read a file as the bytes of its text.

        Args:
            path: The file to read.

        Returns:
            The text of the file encoded as UTF-8, since the ports a view reads
            through give text.

        Raises:
            FileNotFoundError: If the view does not hold the file.
        """
        ...

    def write_text(self, path: Path, text: str) -> None:
        """Refuse to write, because a view only reads.

        Args:
            path: The file.
            text: The content.

        Raises:
            PermissionError: Always.
        """
        ...

    def append_text(self, path: Path, text: str) -> None:
        """Refuse to append, because a view only reads.

        Args:
            path: The file.
            text: The text.

        Raises:
            PermissionError: Always.
        """
        ...

    def exists(self, path: Path) -> bool:
        """Tell whether a file or a directory of the view exists.

        Args:
            path: The path.

        Returns:
            True for a file the view holds and for a directory with such a file
            below it.
        """
        ...

    def is_dir(self, path: Path) -> bool:
        """Tell whether a path is a directory of the view.

        Args:
            path: The path.

        Returns:
            True when a file of the view lies below it.
        """
        ...

    def is_file(self, path: Path) -> bool:
        """Tell whether a path is a file of the view.

        Args:
            path: The path.

        Returns:
            True when the view holds the file.
        """
        ...

    def is_symlink(self, path: Path) -> bool:
        """Tell whether a path is a symbolic link.

        Args:
            path: The path.

        Returns:
            Always false, because a view holds files read as text.
        """
        ...

    def list_dir(self, path: Path) -> Sequence[Path]:
        """List a directory's entries.

        Args:
            path: The directory.

        Returns:
            The files and the directories directly in it, as absolute paths
            sorted by name.

        Raises:
            FileNotFoundError: If the path is not a directory of the view and
                not a file of it.
            NotADirectoryError: If the path is a file of the view.
        """
        ...

class HeadFiles(ReadOnlyFiles):
    """The files of a revision, read through the `History` port.

    It holds every file of the revision, read with one `list_files` the first
    time the view is asked, and reads a file with `show`. A revision that git
    rejects is the caller's to handle, as the port says.
    """

    def __init__(self, history: History, root: Path, revision: str = "HEAD") -> None:
        """Say which revision the view reads.

        Args:
            history: The port that lists and reads the revision.
            root: The absolute path of the repository root.
            revision: The revision, `HEAD` by default.
        """
        ...

class IndexFiles(ReadOnlyFiles):
    """The files that are staged in the index, below a directory.

    The `Repository` port reads one staged file by its path and lists none, so
    the view lists the files below its directory in the working tree and in the
    revision `HEAD` and keeps those that the index holds, read with
    `show_index`. A file that is staged and is in neither place is not in the
    view, and a file that the index lacks is not, whatever the other two hold.
    """

    def __init__(
        self,
        repository: Repository,
        history: History,
        working: FileSystem,
        root: Path,
        below: Path,
    ) -> None:
        """Say where the candidates are listed and what is staged.

        Args:
            repository: The port that reads a staged file.
            history: The port that lists the files of `HEAD`.
            working: The file system of the working tree, listed for candidates.
            root: The absolute path of the repository root.
            below: The directory, relative to the root, below which the view
                lists files, such as the Works directory.
        """
        ...
