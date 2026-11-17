# SPDX-License-Identifier: Apache-2.0
"""Read-only views of a repository as a `FileSystem`.

A view lets the code that reads a tree of files, such as the discovery of Works,
run unchanged on the index or on a revision instead of the working tree. A view
is an adapter of the `FileSystem` port over the `Repository` and `History`
ports, so it is imported only by `wio.cli` and the tests, and it never calls git
itself.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.io.ports import FileSystem, History, Repository


class ReadOnlyFiles(ABC):
    """What the views share: a `FileSystem` over a set of files that is read-only.

    A subclass says which files the view holds and what each contains, and this
    class answers the members of the port from that. A path is absolute, below
    the root the view was given, and a path outside it does not exist. A view
    holds files only, so a directory exists when a file lies below it, and a
    symbolic link never exists.

    A subclass is a dataclass that has a `root` field, the absolute path of the
    repository root that the paths of the view are relative to, among the fields
    it needs, in the order that suits its caller.
    """

    root: Path

    @abstractmethod
    def paths(self) -> frozenset[Path]:
        """List the files that the view holds.

        Returns:
            Their paths relative to the root. A subclass reads them once and
            keeps them, so every member answers from one listing.
        """

    @abstractmethod
    def content(self, path: Path) -> str | None:
        """Read one file of the view.

        Args:
            path: A file that `paths` lists, relative to the root.

        Returns:
            The file's content as stored, or `None` when the view does not hold
            it.
        """

    def read_text(self, path: Path) -> str:
        """Read a file as UTF-8 text.

        Args:
            path: The file to read.

        Returns:
            The file's content, with its line ends as stored.

        Raises:
            FileNotFoundError: If the view does not hold the file.
        """
        relative = self._relative(path)
        text = self.content(relative) if self.is_file(path) else None
        if text is None:
            raise FileNotFoundError(path)
        return text

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
        return bytes(self.read_text(path), "utf-8")

    def write_text(self, path: Path, text: str) -> None:  # noqa: ARG002
        """Refuse to write, because a view only reads.

        Args:
            path: The file.
            text: The content.

        Raises:
            PermissionError: Always.
        """
        raise _read_only(path)

    append_text = write_text

    def exists(self, path: Path) -> bool:
        """Tell whether a file or a directory of the view exists.

        Args:
            path: The path.

        Returns:
            True for a file the view holds and for a directory with such a file
            below it.
        """
        return self.is_file(path) or self.is_dir(path)

    def is_dir(self, path: Path) -> bool:
        """Tell whether a path is a directory of the view.

        Args:
            path: The path.

        Returns:
            True when a file of the view lies below it.
        """
        relative = self._relative(path)
        parts = relative.parts
        return any(
            p.parts[: len(parts)] == parts and p != relative for p in self.paths()
        )

    def is_file(self, path: Path) -> bool:
        """Tell whether a path is a file of the view.

        Args:
            path: The path.

        Returns:
            True when the view holds the file.
        """
        return self._relative(path) in self.paths()

    def is_symlink(self, path: Path) -> bool:  # noqa: ARG002
        """Tell whether a path is a symbolic link.

        Args:
            path: The path.

        Returns:
            Always false, because a view holds files read as text.
        """
        return False

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
        if self.is_file(path):
            raise NotADirectoryError(path)
        if not self.is_dir(path):
            raise FileNotFoundError(path)
        parts = self._relative(path).parts
        names = {
            p.parts[len(parts)]
            for p in self.paths()
            if p.parts[: len(parts)] == parts and len(p.parts) > len(parts)
        }
        return [path / name for name in sorted(names)]

    def _relative(self, path: Path) -> Path:
        """Make a path relative to the root of the view.

        Args:
            path: An absolute path, or one that is relative to the root.

        Returns:
            The path below the root, which no file of the view has when the path
            is outside the root.
        """
        try:
            return path.relative_to(self.root)
        except ValueError:
            return Path("..") / path.name


@dataclass(eq=False)
class HeadFiles(ReadOnlyFiles):
    """The files of a revision, read through the `History` port.

    It holds every file of the revision, read with one `list_files` the first
    time the view is asked, and reads a file with `show`. A revision that git
    rejects is the caller's to handle, as the port says.

    Attributes:
        history: The port that lists and reads the revision.
        root: The absolute path of the repository root.
        revision: The revision, `HEAD` by default.
    """

    history: History
    root: Path
    revision: str = "HEAD"
    _listing: frozenset[Path] | None = field(default=None, init=False, repr=False)

    def paths(self) -> frozenset[Path]:
        """List the files of the revision.

        Returns:
            Their paths relative to the root, read once.
        """
        if self._listing is None:
            self._listing = frozenset(self.history.list_files(self.revision))
        return self._listing

    def content(self, path: Path) -> str | None:
        """Read one file of the revision.

        Args:
            path: A file of the revision, relative to the root.

        Returns:
            The file's content, or `None` when the revision has none.
        """
        return self.history.show(self.revision, path)


@dataclass(eq=False)
class IndexFiles(ReadOnlyFiles):
    """The files that are staged in the index, below a directory.

    The `Repository` port reads one staged file by its path and lists none, so
    the view lists the files below its directory in the working tree and in the
    revision `HEAD` and keeps those that the index holds, read with
    `show_index`. A file that is staged and is in neither place is not in the
    view, and a file that the index lacks is not, whatever the other two hold.

    Attributes:
        repository: The port that reads a staged file.
        history: The port that lists the files of `HEAD`.
        working: The file system of the working tree, listed for candidates.
        root: The absolute path of the repository root.
        below: The directory, relative to the root, below which the view lists
            files, such as the Works directory.
    """

    repository: Repository
    history: History
    working: FileSystem
    root: Path
    below: Path

    def paths(self) -> frozenset[Path]:
        """List the files below the directory that the index holds.

        Returns:
            Their paths relative to the root.
        """
        held = (c for c in self.candidates() if self.content(c) is not None)
        return frozenset(held)

    def candidates(self) -> frozenset[Path]:
        """List the files below the directory that the working tree or `HEAD` has.

        Returns:
            Their paths relative to the root, whether or not the index holds
            them.
        """
        raise NotImplementedError

    def content(self, path: Path) -> str | None:
        """Read one staged file.

        Args:
            path: A file below the directory, relative to the root.

        Returns:
            The staged content, or `None` when the index has none.
        """
        return self.repository.show_index(path)


def _read_only(path: Path) -> PermissionError:
    """Make the error of a write to a view.

    Args:
        path: The path that was written to.

    Returns:
        The error to raise.
    """
    return PermissionError(f"{path}: a view of a repository is read-only")
