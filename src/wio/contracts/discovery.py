# SPDX-License-Identifier: Apache-2.0
"""Finding the Works of a project, and saying why a file is not one."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.io.walk import refuse_directory, walk_markdown
from wio.models.diagnostics import order_diagnostics

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from pathlib import Path

    from wio.io.ports import FileSystem
    from wio.models.config import Works as WorksSettings
    from wio.models.diagnostics import Diagnostic
    from wio.models.works import Work

_DEFAULT_DIR = ".agents/wio/works"


@dataclass(frozen=True)
class WorkDiscovery:
    """What one walk of the Works directory found.

    It is immutable. Every command that reads Works gets this value from
    `discover_works`, and no command walks the directory on its own.

    Attributes:
        works: The Works found, sorted by the string of their paths. A Work with
            a problem of its own that does not keep it from being identified is
            here, so its children and dependents are not orphaned.
        left_out: The paths of the files left out for an error of their own,
            relative to the repository root and sorted as the Works are. It
            includes a file that cannot be read or decoded, which is not known
            to be marked, and a marked file that a nesting collision or the
            Works directory also excludes: `left_out` takes precedence over
            `excluded`.
        excluded: The paths of the marked files that a nesting collision or the
            Works directory excludes and that are not in `left_out`, relative to
            the repository root and sorted as the Works are. `left_out` and
            `excluded` are disjoint, and with `works` hold every file that
            discovery read a block of or failed to read.
        diagnostics: Every problem found, each an error that names its place,
            ordered as the shared ordering of diagnostics orders them.
        incomplete: The diagnostics that leave the tree incomplete, a subset of
            `diagnostics` in the same order: a Work left out, a nesting
            collision, a marked file directly in the Works directory and a Works
            directory that cannot be walked. A command that refuses every call on
            an incomplete tree tests whether this is empty and reads no message.
        ambiguous: The errors of a shared id, a subset of `diagnostics` in the
            same order. A command that refuses only the lookup of that id uses
            `find_work`, and one that refuses the whole tree for it tests this
            as well. A wrong optional field is in neither, because its Work stays
            in the tree.
    """

    works: tuple[Work, ...]
    left_out: tuple[Path, ...]
    excluded: tuple[Path, ...]
    diagnostics: tuple[Diagnostic, ...]
    incomplete: tuple[Diagnostic, ...]
    ambiguous: tuple[Diagnostic, ...]


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
        The Works, `left_out`, `excluded` and the diagnostics. A Works directory
        that is missing and is the default, or is empty, holds no Work and gives
        no diagnostic; any other that cannot be walked gives one error whose
        message begins `The Works directory`, and no Work.
    """
    directory = root / settings.dir
    refusal = refuse_directory(
        directory, settings.dir, files, noun="Works", default=_DEFAULT_DIR
    )
    if refusal is not None:
        return _refused(refusal)
    if not files.is_dir(directory):
        return _refused([])
    reads = [_read_file(root, path, files) for path in walk_markdown(directory, files)]
    return _assemble(reads, _find_collisions(reads, settings.hierarchy, settings.dir))


def _assemble(reads: Sequence[_Read], collisions: _Collisions) -> WorkDiscovery:
    """Put what the leaves gave into one result.

    Args:
        reads: Every file of the walk, in the order of the walk.
        collisions: What the nesting rules exclude.

    Returns:
        The Works that stay, `left_out` and `excluded` as disjoint lists, and the
        diagnostics, those that leave the tree incomplete and those of a shared
        id, each ordered.
    """
    works = _works_of(reads, collisions.excluded)
    left_out = [read for read in reads if read.left_out]
    excluded = [
        read for read in reads if read.path in collisions.excluded and not read.left_out
    ]
    ambiguous = order_diagnostics(_shared_ids(works))
    incomplete = order_diagnostics(
        [*(d for read in left_out for d in read.problems), *collisions.diagnostics]
    )
    every = order_diagnostics(
        [
            *(d for read in reads for d in read.problems),
            *collisions.diagnostics,
            *ambiguous,
        ]
    )
    return WorkDiscovery(
        works, _paths(left_out), _paths(excluded), every, incomplete, ambiguous
    )


def _works_of(reads: Sequence[_Read], excluded: frozenset[Path]) -> tuple[Work, ...]:
    """Pick the Works that stay in the tree.

    Args:
        reads: Every file of the walk.
        excluded: The files that the nesting rules exclude.

    Returns:
        The Works of the reads that are not excluded, sorted by their paths.
    """
    kept = (read.work for read in reads if read.path not in excluded)
    return tuple(sorted((work for work in kept if work), key=_by_path))


@dataclass(frozen=True)
class _Read:
    """What reading one file gave.

    Attributes:
        path: The file, relative to the repository root.
        marked: Whether the file is known to be marked: its block was found,
            even if it could not be read. A file that cannot be read or decoded
            is not.
        left_out: Whether the file is left out, so that it has no `work`.
        work: The Work built from the file, or `None` when it is not marked or
            is left out.
        problems: The errors of this file alone, whether it is left out or its
            Work stays with a wrong optional field.
    """

    path: Path
    marked: bool
    left_out: bool
    work: Work | None
    problems: tuple[Diagnostic, ...]


@dataclass(frozen=True)
class _Collisions:
    """What the nesting rules exclude.

    Attributes:
        excluded: The marked files of a directory with two or more, and those
            directly in the Works directory, counting a file that is left out.
        diagnostics: The error of each directory and of each such file. Empty
            under `flat`.
    """

    excluded: frozenset[Path]
    diagnostics: tuple[Diagnostic, ...]


def _refused(problems: Sequence[Diagnostic]) -> WorkDiscovery:
    """Build the result of a Works directory that holds no Work.

    Args:
        problems: The error of a directory that cannot be walked, or none.

    Returns:
        An empty discovery whose only diagnostics, all of them incomplete, are
        the problems.
    """
    ordered = order_diagnostics(problems)
    return WorkDiscovery((), (), (), ordered, ordered, ())


def _by_path(work: Work) -> str:
    """Give the key that sorts Works by the string of their paths.

    Args:
        work: A Work.

    Returns:
        The string of its path.
    """
    return str(work.path)


def _paths(reads: Iterable[_Read]) -> tuple[Path, ...]:
    """List the paths of some reads in the order of their strings.

    Args:
        reads: The reads.

    Returns:
        Their paths, sorted as the Works are.
    """
    return tuple(sorted((read.path for read in reads), key=str))


def _read_file(root: Path, path: Path, files: FileSystem) -> _Read:
    """Read one file of the walk into a `_Read`: the leaf of AC-1 to AC-3.

    It reads the block, the title and the optional fields, reports a file that
    cannot be identified once, and an optional field of a wrong type once, and
    builds the Work with that field empty.

    Args:
        root: The repository root, which the places and paths are relative to.
        path: The file.
        files: The port that reads it.

    Returns:
        The read.
    """
    raise NotImplementedError


def _find_collisions(
    reads: Sequence[_Read], hierarchy: str, works_dir: str
) -> _Collisions:
    """Apply the nesting rules to the files that were read: the leaf of AC-5, AC-6.

    Args:
        reads: Every file of the walk, in the order of the walk.
        hierarchy: `flat` or `nesting`.
        works_dir: The Works directory as written, relative to the root.

    Returns:
        The excluded files and their errors, none under `flat`.
    """
    raise NotImplementedError


def _shared_ids(works: Sequence[Work]) -> tuple[Diagnostic, ...]:
    """Report the ids that two or more Works share: the leaf of AC-4.

    Args:
        works: The Works that stay in the tree, sorted by their paths. A Work
            that a nesting collision excludes is not among them and shares an id
            with none.

    Returns:
        One error for each shared id, at the paths of its Works in that order,
        joined by `, `, which is the place that `find_work` looks for.
    """
    raise NotImplementedError


def find_work(discovery: WorkDiscovery, work_id: str) -> Work | Diagnostic | None:
    """Look a Work up by its id in what discovery found.

    Args:
        discovery: The result of `discover_works`.
        work_id: The id to look up, compared as text.

    Returns:
        The Work that has the id, the error of `ambiguous` whose place joins the
        paths of the Works that share the id, never a message read for the id,
        when two or more Works share it, so that the lookup is refused and
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
    reads files only through `files` and writes none. It reads the tree again and
    does not take a `WorkDiscovery`, so a command that has one pays for a second
    walk.

    Args:
        root: The repository root.
        path: The path, absolute or relative to `root`.
        settings: The `[works]` table of the config.
        files: The port that reads files and reports what a path is.

    Returns:
        The reason, or `None` when the path is a Work.
    """
    raise NotImplementedError
