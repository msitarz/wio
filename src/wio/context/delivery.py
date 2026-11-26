# SPDX-License-Identifier: Apache-2.0
"""Delivery of context bundles to files."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
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
    """Write a bundle and give its displayed path and warnings.

    Args:
        bundle: The bundle to write.
        path: A path as given or None for the default.
        repository: Finds the worktree and clone.
        files: Resolves paths and writes the file.
        directories: Finds the temporary directory.

    Raises:
        NotImplementedError: Until file delivery is implemented.
    """
    message = "bundle file delivery"
    raise NotImplementedError(message)
