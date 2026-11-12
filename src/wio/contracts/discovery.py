# SPDX-License-Identifier: Apache-2.0
"""Finding the Works of a project, and saying why a file is not one."""

from dataclasses import dataclass
from functools import partial
from itertools import chain
from os.path import normpath
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from wio.formats.errors import MetadataBlockError
from wio.io.walk import refuse_directory, walk_markdown
from wio.models.diagnostics import Diagnostic, order_diagnostics
from wio.models.frozen import freeze
from wio.models.works import Work
lazy from wio.formats import read_metadata_block, read_outline

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping, Sequence

    from wio.io.ports import FileSystem
    from wio.models.block import MetadataBlock
    from wio.models.config import Works as WorksSettings

_DEFAULT_DIR = ".agents/wio/works"
_SUFFIX = ".md"
_error = partial(Diagnostic, "error")
"""Make an error diagnostic from a place and a message."""
_DIRECT = "A Work cannot sit directly in the Works directory"
_ACTIONS = (
    "`[actions]` must be a table whose values are a string or an array of strings"
)


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
    return _assemble(*_read_tree(root, directory, settings, files))


def _read_tree(
    root: Path, directory: Path, settings: WorksSettings, files: FileSystem
) -> tuple[list[_Read], _Collisions]:
    """Read every file of the walk and apply the nesting rules to them.

    Args:
        root: The repository root.
        directory: The Works directory, joined to the root, which can be walked.
        settings: The `[works]` table.
        files: The port that lists and reads.

    Returns:
        The reads in the order of the walk, and what the nesting rules exclude.
    """
    reads = [_read_file(root, path, files) for path in walk_markdown(directory, files)]
    return reads, _find_collisions(reads, settings.hierarchy, settings.dir)


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
        groups: The marked files of each directory that holds two or more, each
            group sorted, so that a reason can name the others without reading a
            message.
        direct: The marked files directly in the Works directory.
    """

    excluded: frozenset[Path]
    diagnostics: tuple[Diagnostic, ...]
    groups: tuple[tuple[Path, ...], ...] = ()
    direct: frozenset[Path] = frozenset()


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


def _place(root: Path, path: Path) -> str:
    """Write a file's place: its path relative to the root, with `/`.

    Args:
        root: The repository root.
        path: The file.

    Returns:
        The place of a diagnostic about the file.
    """
    return PurePosixPath(path.relative_to(root)).as_posix()


def _unidentified(path: Path, *, marked: bool, problem: Diagnostic) -> _Read:
    """Build the read of a file that is left out.

    Args:
        path: The file, relative to the root.
        marked: Whether the file is known to be marked.
        problem: The one error that leaves it out.

    Returns:
        A read with no Work and that error.
    """
    return _Read(path, marked=marked, left_out=True, work=None, problems=(problem,))


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
    place = _place(root, path)
    relative = path.relative_to(root)
    try:
        block = read_metadata_block(files.read_text(path))
    except UnicodeDecodeError:
        return _unidentified(
            relative,
            marked=False,
            problem=_error(place, "The file is not valid UTF-8"),
        )
    except OSError as error:
        reason = f"The file cannot be read: {error.strerror}"
        return _unidentified(relative, marked=False, problem=_error(place, reason))
    except MetadataBlockError as error:
        return _unidentified(
            relative,
            marked=True,
            problem=_error(f"{place}:{error.line}", error.message),
        )
    if block is None:
        return _Read(relative, marked=False, left_out=False, work=None, problems=())
    return _read_block(relative, place, block)


def _read_block(relative: Path, place: str, block: MetadataBlock) -> _Read:
    """Build the read of a marked file whose block was read.

    Args:
        relative: The file, relative to the root.
        place: The file's place.
        block: Its metadata block and body.

    Returns:
        A read that is left out when the `id` is missing, not a string or empty,
        and else one with the Work, whose wrong optional fields are empty and
        reported.
    """
    identity = _identity(place, block.data)
    if isinstance(identity, Diagnostic):
        return _unidentified(relative, marked=True, problem=identity)
    fields = _optional_fields(place, block.data)
    headings = read_outline(block.body, block.body_start_line)
    work = Work(
        id=identity,
        title=headings[0].text if headings else None,
        path=relative,
        template=fields.template,
        roots=fields.roots,
        depends_on=fields.depends_on,
        actions=fields.actions,
    )
    return _Read(
        relative, marked=True, left_out=False, work=work, problems=fields.problems
    )


def _identity(place: str, data: Mapping[str, object]) -> str | Diagnostic:
    """Judge the `id` of a block.

    Args:
        place: The file's place.
        data: The decoded block.

    Returns:
        The id, or the error for an id that is missing, not a string or empty.
    """
    if "id" not in data:
        return _error(place, "A Work needs an `id`")
    value = data["id"]
    if not isinstance(value, str):
        return _error(place, "`id` must be a string")
    return value or _error(place, "`id` must not be empty")


@dataclass(frozen=True)
class _Optional:
    """The optional keys of a block as a Work holds them.

    Attributes:
        template: The `template`, or `None`.
        roots: The `roots`, empty when absent or of a wrong shape.
        depends_on: The `depends_on`, empty when absent or of a wrong shape.
        actions: The `[actions]` table, empty when absent or of a wrong shape.
        problems: One error for each key of a wrong shape.
    """

    template: str | None
    roots: tuple[str, ...]
    depends_on: tuple[str, ...]
    actions: frozendict[str, str | tuple[str, ...]]
    problems: tuple[Diagnostic, ...]


def _optional_fields(place: str, data: Mapping[str, object]) -> _Optional:
    """Read the optional keys of a block, each empty when of a wrong shape.

    Args:
        place: The file's place.
        data: The decoded block.

    Returns:
        The template, the roots, the dependencies and the actions, and one error
        for each key of a wrong shape.
    """
    template, wrong_template = _template_field(place, data)
    roots, wrong_roots = _list_field(place, data, "roots")
    depends_on, wrong_depends = _list_field(place, data, "depends_on")
    actions, wrong_actions = _actions_field(place, data)
    return _Optional(
        template,
        roots,
        depends_on,
        actions,
        (*wrong_template, *wrong_roots, *wrong_depends, *wrong_actions),
    )


def _template_field(
    place: str, data: Mapping[str, object]
) -> tuple[str | None, tuple[Diagnostic, ...]]:
    """Read the `template` key.

    Args:
        place: The file's place.
        data: The decoded block.

    Returns:
        The template, or `None` when it is absent or not a string, and the error
        for a key that is present and not a string.
    """
    value = data.get("template")
    if isinstance(value, str):
        return value, ()
    wrong = (_error(place, "`template` must be a string"),)
    return None, wrong if "template" in data else ()


def _list_field(
    place: str, data: Mapping[str, object], key: str
) -> tuple[tuple[str, ...], tuple[Diagnostic, ...]]:
    """Read a key that holds an array of strings.

    Args:
        place: The file's place.
        data: The decoded block.
        key: The key, `roots` or `depends_on`.

    Returns:
        The strings, empty when the key is absent or of a wrong shape, and the
        error for a key that is present and of a wrong shape.
    """
    found = _strings(data.get(key))
    if found is not None:
        return found, ()
    wrong = (_error(place, f"`{key}` must be an array of strings"),)
    return (), wrong if key in data else ()


def _actions_field(
    place: str, data: Mapping[str, object]
) -> tuple[frozendict[str, str | tuple[str, ...]], tuple[Diagnostic, ...]]:
    """Read the `[actions]` key.

    Args:
        place: The file's place.
        data: The decoded block.

    Returns:
        The table, empty when the key is absent or of a wrong shape, and the
        error for a key that is present and of a wrong shape.
    """
    found = _actions(data.get("actions"))
    if found is not None:
        return freeze(found), ()
    wrong = (_error(place, _ACTIONS),)
    return freeze({}), wrong if "actions" in data else ()


def _strings(value: object) -> tuple[str, ...] | None:
    """Read an array of strings.

    Args:
        value: What the block holds, or `None` for an absent key.

    Returns:
        The strings, or `None` when the value is not an array of strings only.
    """
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        return None
    return tuple(value)


def _actions(value: object) -> dict[str, str | tuple[str, ...]] | None:
    """Read the `[actions]` table.

    Args:
        value: What the block holds, or `None` for an absent key.

    Returns:
        The table with each value a string or a tuple of strings, or `None` when
        it is not a table or one value is of another shape.
    """
    if not isinstance(value, dict):
        return None
    table: dict[str, str | tuple[str, ...]] = {}
    for key, entry in value.items():
        found = entry if isinstance(entry, str) else _strings(entry)
        if found is None:
            return None
        table[str(key)] = found
    return table


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
    if hierarchy != "nesting":
        return _Collisions(frozenset(), ())
    direct, others = _split_direct(reads, Path(works_dir))
    crowded = _crowded(others)
    shut = frozenset(read.path for read in chain(direct, *crowded.values()))
    return _Collisions(
        shut,
        _collision_errors(direct, crowded, works_dir),
        tuple(tuple(sorted(r.path for r in group)) for group in crowded.values()),
        frozenset(read.path for read in direct),
    )


def _collision_errors(
    direct: Iterable[_Read], crowded: Mapping[Path, Sequence[_Read]], works_dir: str
) -> tuple[Diagnostic, ...]:
    """Report the files directly in the Works directory and the crowded ones.

    Args:
        direct: The marked files directly in the Works directory.
        crowded: The marked files of each directory that holds two or more.
        works_dir: The Works directory as written.

    Returns:
        One error for each direct file, then one for each crowded directory.
    """
    return (
        *(_direct_error(read, works_dir) for read in direct),
        *(_crowd_error(d, group) for d, group in crowded.items()),
    )


def _split_direct(reads: Iterable[_Read], top: Path) -> tuple[list[_Read], list[_Read]]:
    """Split the marked files into those directly in the Works directory and the rest.

    Args:
        reads: Every file of the walk.
        top: The Works directory, relative to the root.

    Returns:
        The marked files directly in the Works directory, and the other marked
        files.
    """
    marked = [read for read in reads if read.marked]
    direct = [read for read in marked if read.path.parent == top]
    return direct, [read for read in marked if read not in direct]


def _crowded(reads: Iterable[_Read]) -> dict[Path, list[_Read]]:
    """Group marked files by directory and keep the directories with two or more.

    Args:
        reads: The marked files that are not directly in the Works directory.

    Returns:
        The files of each such directory, by the directory.
    """
    by_directory: dict[Path, list[_Read]] = {}
    for read in reads:
        by_directory.setdefault(read.path.parent, []).append(read)
    return {d: group for d, group in by_directory.items() if len(group) > 1}


def _direct_error(read: _Read, works_dir: str) -> Diagnostic:
    """Report a marked file that sits directly in the Works directory.

    Args:
        read: The file.
        works_dir: The Works directory as written.

    Returns:
        The error at the file.
    """
    return _error(
        read.path.as_posix(),
        f"{_DIRECT} `{works_dir}`",
    )


def _crowd_error(directory: Path, group: Sequence[_Read]) -> Diagnostic:
    """Report a directory that holds two or more marked files.

    Args:
        directory: The directory, relative to the root.
        group: Its marked files.

    Returns:
        The error at all of them, joined by `, `.
    """
    place = ", ".join(sorted(read.path.as_posix() for read in group))
    return _error(
        place,
        f"`{directory.as_posix()}` holds {len(group)} marked files, "
        "and under `nesting` a directory holds one Work",
    )


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
    by_id: dict[str, list[Work]] = {}
    for work in works:
        by_id.setdefault(work.id, []).append(work)
    return tuple(
        _error(_shared_place(group), f"Works share the id `{work_id}`")
        for work_id, group in by_id.items()
        if len(group) > 1
    )


def _shared_place(group: Sequence[Work]) -> str:
    """Write the place of the error of a shared id.

    Args:
        group: The Works that share it, sorted by their paths.

    Returns:
        Their paths, written with `/` and joined by `, `.
    """
    return ", ".join(work.path.as_posix() for work in group)


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
    matches = [work for work in discovery.works if work.id == work_id]
    if len(matches) > 1:
        place = _shared_place(matches)
        return next(d for d in discovery.ambiguous if d.where == place)
    return matches[0] if matches else None


def _shown(root: Path, absolute: Path) -> str:
    """Write a path as a reason names it: relative to the root when it is below.

    Args:
        root: The repository root.
        absolute: The absolute path.

    Returns:
        The path with `/`, relative to the root when it is below it.
    """
    if root in absolute.parents:
        return PurePosixPath(absolute.relative_to(root)).as_posix()
    return PurePosixPath(absolute).as_posix()


def _path_reasons(
    root: Path, absolute: Path, settings: WorksSettings, files: FileSystem
) -> Iterator[str | None]:
    """Judge a path in the order of the list, the cheapest question first.

    Args:
        root: The repository root.
        absolute: The path, absolute.
        settings: The `[works]` table.
        files: The port that reports what a path is and reads it.

    Yields:
        For each question of the list up to the block, the reason when it applies
        and `None` when it does not, one at a time so that a later question reads
        nothing when an earlier one applies.
    """
    shown = _shown(root, absolute)
    works = root / settings.dir
    yield _not_a_file(shown, absolute, files)
    yield _not_markdown(shown, absolute)
    yield _through_a_link(root, shown, absolute, files)
    yield _outside(shown, absolute, works, settings.dir)
    yield _hidden(shown, absolute, works)
    yield _no_block(shown, absolute, files)


def _not_a_file(shown: str, absolute: Path, files: FileSystem) -> str | None:
    """Judge whether a path is a file that exists.

    Args:
        shown: The path as a reason writes it.
        absolute: The path.
        files: The port.

    Returns:
        The reason, or `None` for a file.
    """
    if files.exists(absolute) and not files.is_dir(absolute):
        return None
    return f"`{shown}` does not exist or is not a file"


def _not_markdown(shown: str, absolute: Path) -> str | None:
    """Judge whether a name ends in `.md`.

    Args:
        shown: The path as a reason writes it.
        absolute: The path.

    Returns:
        The reason, or `None` for a name that ends in `.md`.
    """
    if absolute.name.endswith(_SUFFIX):
        return None
    return f"`{shown}` is not a Markdown file: its name must end in `{_SUFFIX}`"


def _through_a_link(
    root: Path, shown: str, absolute: Path, files: FileSystem
) -> str | None:
    """Judge whether a path is or runs through a symbolic link.

    Only the part below the root is asked about, so that a link in the path of
    the repository itself is not a reason.

    Args:
        root: The repository root.
        shown: The path as a reason writes it.
        absolute: The path.
        files: The port.

    Returns:
        The reason, or `None` when no part of the path below the root is a link.
    """
    inside = root in absolute.parents
    chain_of_parts = (absolute, *absolute.parents) if inside else (absolute,)
    for part in chain_of_parts:
        if part == root:
            break
        if files.is_symlink(part):
            return (
                f"`{shown}` is or runs through the symbolic link `{_shown(root, part)}`"
            )
    return None


def _outside(shown: str, absolute: Path, works: Path, written: str) -> str | None:
    """Judge whether a path is below the Works directory.

    Args:
        shown: The path as a reason writes it.
        absolute: The path.
        works: The Works directory, joined to the root.
        written: The Works directory as written.

    Returns:
        The reason, or `None` for a path below it.
    """
    if works in absolute.parents:
        return None
    return f"`{shown}` is outside the Works directory `{written}`"


def _hidden(shown: str, absolute: Path, works: Path) -> str | None:
    """Judge whether a path is under a hidden directory below the Works directory.

    Args:
        shown: The path as a reason writes it.
        absolute: The path, which is below the Works directory.
        works: The Works directory, joined to the root.

    Returns:
        The reason naming the first hidden directory, or `None`.
    """
    below = absolute.relative_to(works).parent.parts
    hidden = next((name for name in below if name.startswith(".")), None)
    if hidden is None:
        return None
    return (
        f"`{shown}` is under the hidden directory `{hidden}` below the Works directory"
    )


def _no_block(shown: str, absolute: Path, files: FileSystem) -> str | None:
    """Judge whether a file has no metadata block of wio's.

    Args:
        shown: The path as a reason writes it.
        absolute: The file.
        files: The port that reads it.

    Returns:
        The reason when there is no block on the first line, or the `+++` front
        matter has no `wio` key, and `None` for a file that cannot be read, whose
        block cannot be read, or that has a block.
    """
    try:
        text = files.read_text(absolute)
        block = read_metadata_block(text)
    except UnicodeDecodeError, OSError, MetadataBlockError:
        return None
    if block is not None:
        return None
    first = text.removeprefix("\ufeff").partition("\n")[0].rstrip()
    if first == "+++":
        return f"`{shown}` has `+++` front matter with no `wio` key"
    return f"`{shown}` has no metadata block that starts on its first line"


def _tree_reason(
    root: Path, absolute: Path, settings: WorksSettings, files: FileSystem
) -> str | None:
    """Judge a path that is a Markdown file below the Works directory by the tree.

    The reasons come from what was read and from the nesting rules, and no
    message of a diagnostic is read, so a file name that holds `:` or `, ` is
    judged like any other.

    Args:
        root: The repository root.
        absolute: The path, below the Works directory.
        settings: The `[works]` table.
        files: The port.

    Returns:
        The reason a collision, the Works directory or an error of its own gives,
        or `None` for a Work.
    """
    reads, collisions = _read_tree(root, root / settings.dir, settings, files)
    relative = absolute.relative_to(root)
    return (
        _crowd_reason(collisions.groups, relative)
        or _direct_reason(collisions.direct, relative, settings.dir)
        or _own_reason(reads, relative)
    )


def _crowd_reason(groups: Iterable[Sequence[Path]], relative: Path) -> str | None:
    """Say that a file shares its directory with other marked files.

    Args:
        groups: The marked files of each directory that holds two or more.
        relative: The file, relative to the root.

    Returns:
        The reason naming the other files, or `None`.
    """
    for group in groups:
        if relative in group:
            others = ", ".join(p.as_posix() for p in group if p != relative)
            return (
                f"`{relative.as_posix()}` is in a directory with other marked "
                f"files: {others}"
            )
    return None


def _direct_reason(
    direct: Iterable[Path], relative: Path, works_dir: str
) -> str | None:
    """Say that a marked file sits directly in the Works directory.

    Args:
        direct: The marked files directly in the Works directory.
        relative: The file, relative to the root.
        works_dir: The Works directory as written.

    Returns:
        The reason naming the directory, or `None`.
    """
    if relative not in direct:
        return None
    return (
        f"`{relative.as_posix()}` is directly in the Works directory "
        f"`{works_dir}`, where a Work cannot sit"
    )


def _own_reason(reads: Iterable[_Read], relative: Path) -> str | None:
    """Say that a file is left out for an error of its own.

    Args:
        reads: Every file of the walk.
        relative: The file, relative to the root.

    Returns:
        The reason naming that error, or `None`.
    """
    for read in reads:
        if read.path == relative and read.left_out:
            return f"`{relative.as_posix()}` is left out: {read.problems[0].message}"
    return None


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
        path: The path, absolute or relative to `root`, with any `..` collapsed
            as text before it is judged.
        settings: The `[works]` table of the config.
        files: The port that reads files and reports what a path is.

    Returns:
        The reason, or `None` when the path is a Work.
    """
    absolute = Path(normpath(path if path.is_absolute() else root / path))
    for reason in _path_reasons(root, absolute, settings, files):
        if reason is not None:
            return reason
    return _tree_reason(root, absolute, settings, files)
