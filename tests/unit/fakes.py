# SPDX-License-Identifier: Apache-2.0
"""Fakes of the ports that the unit tests of several components share."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING
lazy from pathlib import Path

if TYPE_CHECKING:
    from collections.abc import Sequence


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
