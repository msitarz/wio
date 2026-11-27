# SPDX-License-Identifier: Apache-2.0
"""Delivery of context bundles to files."""

from pathlib import Path
from typing import TYPE_CHECKING

from wio.errors import WioError
from wio.formats.repository_key import repository_key

if TYPE_CHECKING:
    from wio.env.ports import Directories
    from wio.io.ports import FileSystem, Repository
    from wio.models.bundle import CompiledBundle


def _default_path(
    bundle: CompiledBundle, repository: Repository, directories: Directories
) -> Path:
    """Find the clone and bundle's default path."""
    try:
        temporary = directories.temp_dir()
    except OSError as error:
        message = (
            "Cannot use the temporary directory; set $TMPDIR or use --output <path>."
        )
        raise WioError(message) from error
    return temporary / "wio" / repository_key(repository.identity()) / f"{bundle.id}.md"


def write_bundle(
    bundle: CompiledBundle,
    path: str | None,
    repository: Repository,
    files: FileSystem,
    directories: Directories,
) -> tuple[str, tuple[str, ...]]:
    """Write the bundle, returning its displayed path and delivery warnings.

    Args:
        bundle: The bundle to write.
        path: The path as given, or None for the default.
        repository: Finds the worktree and clone identity.
        files: Resolves paths and writes the file.
        directories: Finds the temporary directory.

    Returns:
        The path as displayed and any warning about the worktree.

    Raises:
        WioError: The temporary directory or destination cannot be used.
    """
    destination = (
        _default_path(bundle, repository, directories) if path is None else Path(path)
    )
    displayed = str(destination) if path is None else path
    try:
        inside = files.resolve(destination).is_relative_to(
            files.resolve(repository.root())
        )
        files.write_text(destination, bundle.text)
    except OSError as error:
        hint = "; set $TMPDIR or use --output <path>" if path is None else ""
        message = f"Cannot write bundle to {displayed}: {error}{hint}"
        raise WioError(message) from error
    warning = "The uncommitted bundle can be committed by mistake."
    return displayed, (warning,) if inside else ()
