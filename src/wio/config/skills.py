# SPDX-License-Identifier: Apache-2.0
"""The lookup of a skill's directory and the hash of its files."""

import hashlib
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from wio.config.paths import searched_directories, skill_directory
from wio.models.skill import FoundSkill

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from wio.io.ports import FileSystem, Repository
    from wio.ports import Settings


@dataclass(frozen=True)
class RepositorySkills:
    """Finds the skills of the repository.

    It satisfies the `SkillLookup` port of `wio.context`, whose docstring says
    what is found. It reads the working tree and writes nothing. It searches as
    the check of `wio.config` does, so the two agree.

    The hash is the SHA-256 of, for every regular file below the skill's
    directory at any depth, in the order of the UTF-8 bytes of their relative
    paths written with `/`: the path, a NUL byte, the file's bytes and a NUL
    byte. A symbolic link below the directory counts for nothing, neither as a
    file nor as a directory to look into.

    Attributes:
        repository: Finds the repository root.
        files: Lists and reads the files of a skill.
        settings: Gives `[skills] paths`.
    """

    repository: Repository
    files: FileSystem
    settings: Settings

    def find_skill(self, name: str) -> FoundSkill | None:
        """Find a skill and hash its files.

        Args:
            name: The skill's name.

        Returns:
            The skill's directory and files hash, or `None` when it is not
            found.

        Raises:
            ConfigurationError: If the settings cannot be loaded.
            OSError: If a file of the skill cannot be listed or read.
        """
        searched = searched_directories(self.settings.load().skills.paths)
        root = self.repository.root()
        parent = skill_directory(name, searched, root, self.files)
        if parent is None:
            return None
        directory = (PurePosixPath(parent) / name).as_posix()
        return FoundSkill(directory, _files_hash(root / directory, self.files))


def _files_hash(directory: Path, files: FileSystem) -> str:
    """Hash the files of a skill, as `RepositorySkills` says.

    Args:
        directory: The skill's directory.
        files: Lists and reads what is in it.

    Returns:
        The 64 lower-case hexadecimal digits.

    Raises:
        OSError: If a file cannot be listed or read.
    """
    digest = hashlib.sha256()
    named = sorted(
        (path.relative_to(directory).as_posix().encode(errors="surrogateescape"), path)
        for path in _regular_files(directory, files)
    )
    for name, path in named:
        digest.update(b"\0".join((name, files.read_bytes(path), b"")))
    return digest.hexdigest()


def _regular_files(directory: Path, files: FileSystem) -> Iterator[Path]:
    """Find every regular file below a directory without following links.

    Args:
        directory: The directory, which may itself be a link.
        files: Lists the directories.

    Yields:
        The files at any depth, in no particular order.

    Raises:
        OSError: If a directory cannot be listed.
    """
    for entry in files.list_dir(directory):
        if files.is_symlink(entry):
            continue
        if files.is_dir(entry):
            yield from _regular_files(entry, files)
        elif files.is_file(entry):
            yield entry
