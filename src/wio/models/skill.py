# SPDX-License-Identifier: Apache-2.0
"""The type of a skill that was found in the repository."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FoundSkill:
    """Where a skill is and what its files hold.

    Attributes:
        directory: The skill's directory, relative to the repository root and
            with `/` separators.
        files_hash: The SHA-256, as 64 lower-case hexadecimal digits, of the
            path and the bytes of every regular file below the directory, with
            symbolic links left out. It changes when a file is changed, added,
            removed or renamed, and not with a modification time or a mode.
    """

    directory: str
    files_hash: str
