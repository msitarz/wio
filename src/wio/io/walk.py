# SPDX-License-Identifier: Apache-2.0
"""The walk of a directory of Markdown files, shared by the commands that read one."""

from functools import partial
from typing import TYPE_CHECKING

from wio.models.diagnostics import Diagnostic

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from wio.io.ports import FileSystem

_SUFFIX = ".md"
_error = partial(Diagnostic, "error")
"""Make an error diagnostic from a place and a message."""


def walk_markdown(directory: Path, files: FileSystem) -> Iterator[Path]:
    """List the Markdown files below a directory, in the order of the listing.

    It reads no file. A file is listed when its name ends in `.md` with that
    case, and a symbolic link, a directory whose name starts with `.` and
    anything below it are skipped, and so is anything that is not a file. The
    directory itself is walked whatever its name.

    Args:
        directory: The directory to walk.
        files: The port that lists directories.

    Yields:
        Each file, in the order that the port lists the entries, a directory's
        files where the directory is listed.
    """
    for entry in files.list_dir(directory):
        if files.is_symlink(entry):
            continue
        if files.is_dir(entry):
            yield from _walk_visible(entry, files)
        elif entry.name.endswith(_SUFFIX) and files.is_file(entry):
            yield entry


def _walk_visible(directory: Path, files: FileSystem) -> Iterator[Path]:
    """Walk a directory below the one being walked unless it is hidden.

    Args:
        directory: The directory.
        files: The port that lists directories.

    Yields:
        The files below it, none when its name starts with `.`.
    """
    if not directory.name.startswith("."):
        yield from walk_markdown(directory, files)


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
    if files.is_symlink(directory):
        return [_error(written, f"The {noun} directory must not be a symbolic link")]
    if not files.exists(directory):
        if written == default:
            return None
        return [_error(written, f"The {noun} directory does not exist")]
    if not files.is_dir(directory):
        return [_error(written, f"The {noun} directory is not a directory")]
    return None
