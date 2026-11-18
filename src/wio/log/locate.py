# SPDX-License-Identifier: Apache-2.0
"""Where the log of a repository is, and which files it holds.

The sink that writes events and `show`, which reads them, both ask this module,
so they agree on one location for each clone: shared by every worktree of the
clone, and by no other clone. Nothing here creates a file or a directory; the
first write does.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from wio.env.ports import Directories
    from wio.io.ports import FileSystem, Repository

EVENTS_FILE = "events.jsonl"
"""The one file the sink appends to."""


def log_directory(identity: Path, home: Path) -> Path:
    """Give the directory of the log of one clone under a Wio home.

    The result is `home / "log" / f"{name}-{digest}"`. The digest is the first 12
    lowercase hexadecimal characters of the SHA-256 of the identity as the file
    system encodes it, and alone identifies the clone. The name is for a person:
    the slug of the identity's last component, or of the one before it when that
    is `.git`, without a trailing `.git`; the slug is lowercase, each run of
    characters outside `a-z0-9` is one `-`, it is cut to 40 characters and
    trimmed of `-`, and it is `repo` when nothing is left. It reads no file.

    Args:
        identity: What `Repository.identity` gives.
        home: The Wio home.

    Returns:
        The directory, which may not exist.
    """
    del identity
    del home
    msg = "log_directory"
    raise NotImplementedError(msg)


def locate_log(repository: Repository, directories: Directories) -> Path:
    """Find the directory of the log of the repository the command runs in.

    It creates nothing.

    Args:
        repository: Tells the identity of the clone.
        directories: Tells the Wio home.

    Returns:
        The directory, which may not exist.

    Raises:
        RuntimeError: As `Repository.identity` does, outside a repository.
        ValueError: As `Directories.wio_home` does, for a relative `$WIO_HOME`.
        OSError: As `Directories.wio_home` does, with no home to find.
    """
    msg = "locate_log"
    raise NotImplementedError(msg)


def log_files(directory: Path, filesystem: FileSystem) -> Sequence[Path]:
    """List the files of a log that a reader reads, in a fixed order.

    A file is an entry whose name ends in a lowercase `.jsonl` and that
    `FileSystem.is_file` accepts, which follows a symlink to a file. The order is
    the one `FileSystem.list_dir` gives.

    Args:
        directory: The directory of a log.
        filesystem: Lists the directory.

    Returns:
        The files, empty when the directory does not exist.

    Raises:
        NotADirectoryError: As `FileSystem.list_dir` does, for a file.
    """
    del directory
    del filesystem
    msg = "log_files"
    raise NotImplementedError(msg)
