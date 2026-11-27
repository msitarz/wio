# SPDX-License-Identifier: Apache-2.0
"""The boundary for delivering a compiled bundle to a file."""

from wio.env.ports import Directories
from wio.io.ports import FileSystem, Repository
from wio.models.bundle import CompiledBundle

def write_bundle(
    bundle: CompiledBundle,
    path: str | None,
    repository: Repository,
    files: FileSystem,
    directories: Directories,
) -> tuple[str, tuple[str, ...]]:
    """Write a bundle and return its displayed path and delivery warnings.

    `None` chooses the clone's bundle path under the temporary directory. A
    given path is displayed unchanged. The result's warnings have no prefix or
    newline; a resolved path inside the worktree produces one warning.

    Args:
        bundle: The bundle to write.
        path: The requested path, or None for the default path.
        repository: Gives the worktree root and clone identity.
        files: Resolves paths and writes the bundle.
        directories: Finds the temporary directory for a default path.

    Returns:
        The displayed path and the warnings, in reporting order.

    Raises:
        WioError: The temporary directory or bundle file cannot be used, with
            a message identifying the path and the applicable alternatives.
    """
    ...
