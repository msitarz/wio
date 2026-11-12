# SPDX-License-Identifier: Apache-2.0
"""Finding the Works of a project, and saying why a file is not one."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from wio.io.ports import FileSystem
    from wio.models.config import Works as WorksSettings
    from wio.models.diagnostics import Diagnostic
    from wio.models.works import Work


@dataclass(frozen=True)
class WorkDiscovery:
    """What one walk of the Works directory found.

    It is immutable. Every command that reads Works gets this value from
    `discover_works`, and no command walks the directory on its own.

    Attributes:
        works: The Works found, sorted by the string of their paths. A Work with
            a problem of its own that does not keep it from being identified is
            here, so its children and dependents are not orphaned.
        left_out: The paths of the marked files that were left out, relative to
            the repository root and sorted as the Works are. A file that a
            nesting collision excludes is not one of them.
        diagnostics: Every problem found, each an error that names its place,
            ordered as the shared ordering of diagnostics orders them.
        incomplete: The diagnostics that leave the tree incomplete or ambiguous,
            a subset of `diagnostics` in the same order: a Work left out, a
            shared id, a nesting collision, a marked file directly in the Works
            directory and a Works directory that cannot be walked. A wrong
            optional field is not one, because its Work stays in the tree. A
            command that refuses an incomplete tree tests whether this is empty
            and reads no message to decide.
    """

    works: tuple[Work, ...]
    left_out: tuple[Path, ...]
    diagnostics: tuple[Diagnostic, ...]
    incomplete: tuple[Diagnostic, ...]


def discover_works(
    root: Path, settings: WorksSettings, files: FileSystem
) -> WorkDiscovery:
    """Walk the Works directory and read each marked file into a `Work`.

    The walk is `walk_markdown`'s, after `refuse_directory` has judged the
    directory: it reads files ending in `.md` with that case, skips a directory
    whose name starts with `.` below the Works directory, and follows no
    symbolic link. A file is marked when its metadata block starts on its first
    line. It reads files only through `files` and writes none.

    A file with an error that keeps it from being identified is left out with
    one error: one that cannot be read or decoded, a block that cannot be read,
    a marker of an unknown version, and an `id` that is missing, not a string or
    empty. A key of another type than the block allows (`template`, `roots`,
    `depends_on`, `[actions]` and each value in it) is one error for that key,
    and the Work is built with that field empty and stays. Works that share an
    `id` all stay, with one error that names all their paths.

    Under `hierarchy = "nesting"`, a directory with two or more marked files
    holds no Work and gets one error that names all of them, and a marked file
    directly in the Works directory is not a Work and gets its own error. A
    marked file whose block cannot be read counts, and its own error is reported
    as well; a file that cannot be read or decoded is not known to be marked and
    does not count. Under `flat` neither rule applies.

    Every diagnostic's place is the file's path relative to `root`, written with
    `/`, followed by `:<line>` for a block that cannot be read and by nothing for
    every other problem, or the directory as written for the Works directory.
    The paths of a shared id or of a collision are joined by `, `.

    Args:
        root: The repository root, which `settings.dir` and the paths of the
            Works are relative to.
        settings: The `[works]` table of the config, of which only `dir` and
            `hierarchy` are read.
        files: The port that lists directories and reads files.

    Returns:
        The Works, the marked files left out and the diagnostics. A Works
        directory that is missing and is the default, or is empty, holds no Work
        and gives no diagnostic; any other that cannot be walked gives one error
        whose message begins `The Works directory`, and no Work.
    """
    raise NotImplementedError


def find_work(discovery: WorkDiscovery, work_id: str) -> Work | Diagnostic | None:
    """Look a Work up by its id in what discovery found.

    Args:
        discovery: The result of `discover_works`.
        work_id: The id to look up, compared as text.

    Returns:
        The Work that has the id, the error of discovery that names every path of
        the id when two or more Works share it, so that the lookup is refused and
        no Work is guessed, or `None` when no Work has the id.
    """
    raise NotImplementedError


def explain_not_a_work(
    root: Path, path: Path, settings: WorksSettings, files: FileSystem
) -> str | None:
    """Say why a path that a person names is not a Work.

    The reason is the first of this list that applies, and each names its
    subject: the path does not exist or is not a file; its name does not end in
    `.md`; the path is or runs through a symbolic link; it is outside the Works
    directory; it is under a hidden directory below the Works directory; there
    is no block or it does not start on the first line; the `+++` front matter
    has no `wio` key; the file is in a directory with another marked file, which
    names those files; the file is directly in the Works directory, which names
    the directory; and the file is left out for an error of its own, which
    includes a file that cannot be read or decoded, and names that error. The
    two reasons about a collision apply only under `hierarchy = "nesting"`. It
    reads files only through `files` and writes none.

    Args:
        root: The repository root.
        path: The path, absolute or relative to `root`.
        settings: The `[works]` table of the config.
        files: The port that reads files and reports what a path is.

    Returns:
        The reason, or `None` when the path is a Work.
    """
    raise NotImplementedError
