# SPDX-License-Identifier: Apache-2.0
"""Fakes of the ports that the unit tests of several components share."""

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, TextIO

if TYPE_CHECKING:
    from collections.abc import Sequence

ROOT = Path("/repo")


@dataclass
class MemoryFileSystem:
    """A `FileSystem` over a dictionary of paths to text.

    Only what the loader reads exists; a path that is not a key is missing.
    """

    files: dict[Path, str] = field(default_factory=dict)
    links: set[Path] = field(default_factory=set)
    failure: Exception | None = None
    calls: list[tuple[str, Path]] = field(default_factory=list)

    def read_text(self, path: Path) -> str:
        """Read a file of the dictionary.

        Args:
            path: The file to read.

        Returns:
            Its text.

        Raises:
            FileNotFoundError: The path is not a key.
            Exception: The `failure` the fake was given, whatever the path.
        """
        if self.failure is not None:
            raise self.failure
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def read_bytes(self, path: Path) -> bytes:
        """Read a file of the dictionary as bytes.

        Args:
            path: The file to read.

        Returns:
            Its text, encoded.
        """
        return self.read_text(path).encode("utf-8")

    def write_text(self, path: Path, text: str) -> None:
        """Store a text.

        Args:
            path: The file to write.
            text: Its content.
        """
        self.files[path] = text

    def append_text(self, path: Path, text: str) -> None:
        """Append a text.

        Args:
            path: The file to append to.
            text: What to add.
        """
        self.files[path] = self.files.get(path, "") + text

    def exists(self, path: Path) -> bool:
        """Tell whether a file or a directory that holds one is stored.

        Args:
            path: Any path.

        Returns:
            True when the path is a key or holds one.
        """
        return path in self.files or any(path in key.parents for key in self.files)

    def is_dir(self, path: Path) -> bool:
        """Tell whether a stored file lies below a path.

        Args:
            path: Any path.

        Returns:
            True when the path is the parent, at any depth, of a key, so a
            directory is one that holds a file. The call is recorded.
        """
        self.calls.append(("is_dir", path))
        return any(path in key.parents for key in self.files)

    def is_file(self, path: Path) -> bool:
        """Tell whether a file or a directory that holds one is stored.

        Args:
            path: Any path.

        Returns:
            True when the path is a key.
        """
        return self.exists(path)

    def is_symlink(self, path: Path) -> bool:
        """Tell whether a path was given as a symbolic link.

        Args:
            path: Any path.

        Returns:
            True when the path is in `links`.
        """
        return path in self.links

    def list_dir(self, path: Path) -> Sequence[Path]:
        """List the stored files and the directories directly under a path.

        Args:
            path: The directory.

        Returns:
            The files whose parent is the path and the child of the path that
            holds each deeper file, sorted and without repeats. The call is
            recorded.
        """
        self.calls.append(("list_dir", path))
        found = {
            path / key.relative_to(path).parts[0]
            for key in self.files
            if path in key.parents
        }
        return sorted(found)


@dataclass
class FakeRepository:
    """A `Repository` whose root is fixed, or that is not inside a repository."""

    top: Path | None = ROOT
    message: str = "not inside a git repository: /elsewhere"

    def root(self) -> Path:
        """Find the root.

        Returns:
            The fixed root.

        Raises:
            RuntimeError: The fake is outside any repository.
        """
        if self.top is None:
            raise RuntimeError(self.message)
        return self.top

    def identity(self) -> Path:
        """Find the identity, which is the root's own `.git`.

        Returns:
            The path of the `.git` directory.
        """
        return self.root() / ".git"

    def show_index(self, path: Path) -> str | None:  # noqa: ARG002
        """Read a staged file; nothing is staged.

        Args:
            path: The file.

        Returns:
            None.
        """
        return None

    def is_dirty(self) -> bool:
        """Tell whether the tree is dirty; it never is.

        Returns:
            False.
        """
        return False


@dataclass
class FakeStdio:
    """In-memory standard streams that satisfy the `Stdio` port."""

    stdin: TextIO = field(default_factory=io.StringIO)
    stdout: TextIO = field(default_factory=io.StringIO)
    stderr: TextIO = field(default_factory=io.StringIO)
