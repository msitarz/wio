# SPDX-License-Identifier: Apache-2.0
"""The walk of a directory of Markdown files, shared by the commands that read one."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from wio.io.ports import FileSystem
    from wio.models.diagnostics import Diagnostic


def walk_markdown(directory: Path, files: FileSystem) -> Iterator[Path]:
    """List the Markdown files below a directory, in the order of the listing.

    It reads no file. A file is listed when its name ends in `.md` with that
    case, and a symbolic link, a directory whose name starts with `.` and
    anything below it are skipped, and so is anything that is not a file.

    Args:
        directory: The directory to walk.
        files: The port that lists directories.

    Yields:
        Each file, in the order that the port lists the entries, a directory's
        files where the directory is listed.
    """
    raise NotImplementedError


def refuse_directory(
    directory: Path,
    written: str,
    files: FileSystem,
    *,
    noun: str,
    default: str,
) -> list[Diagnostic] | None:
    """Judge a directory that is about to be walked.

    It reads no file. A directory that is a symbolic link, that is missing and
    is not the default, or that is not a directory is refused with one error.
    A missing directory written as the default is no problem, and holds nothing.

    Args:
        directory: The directory, joined to the root.
        written: The directory as the config writes it, which is the place of
            the error and is compared with `default` as text.
        files: The port that reports what the path is.
        noun: What the directory holds, which opens the message, such as
            `templates` or `Works`.
        default: The directory as written when the config leaves it out.

    Returns:
        A list of the one error, whose message is `The <noun> directory must not
        be a symbolic link`, `The <noun> directory does not exist` or `The <noun>
        directory is not a directory`, or `None` when the directory can be
        walked or is the missing default.
    """
    raise NotImplementedError
