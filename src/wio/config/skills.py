# SPDX-License-Identifier: Apache-2.0
"""The lookup of a skill's directory and the hash of its files."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.io.ports import FileSystem, Repository
    from wio.models.skill import FoundSkill
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
        del name
        raise NotImplementedError
