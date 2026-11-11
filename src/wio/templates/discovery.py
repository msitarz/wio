# SPDX-License-Identifier: Apache-2.0
"""Finding the templates of a project and building a `Template` from each."""

from dataclasses import dataclass
from functools import partial
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from wio.formats.errors import MetadataBlockError
from wio.io.walk import refuse_directory, walk_markdown
from wio.models.diagnostics import Diagnostic, sort_diagnostics
from wio.models.template import Template
lazy from wio.formats import read_metadata_block

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from wio.io.ports import FileSystem
    from wio.models.config import Templates

_DEFAULT_DIR = ".agents/wio/templates"
_SUFFIX = ".md"
_error = partial(Diagnostic, "error")
"""Make an error diagnostic from a place and a message."""


@dataclass(frozen=True)
class Discovery:
    """What one walk of the templates directory found.

    Attributes:
        templates: The templates built, sorted by name. A template with a
            problem of its own is left out, and the others are still here.
        diagnostics: Every problem found, each an error that names its place:
            the file, the two files of a duplicate name, or the directory. They
            are sorted as `sort_diagnostics` sorts them.
    """

    templates: tuple[Template, ...]
    diagnostics: tuple[Diagnostic, ...]


def discover(root: Path, settings: Templates, files: FileSystem) -> Discovery:
    """Walk the templates directory and build a template for each marked file.

    The walk is that of the Works directory: it reads files ending in `.md` with
    their case, skips directories whose names start with `.`, follows no
    symbolic link, and takes a file for a template when its metadata block starts
    on its first line. A template is named by its file. It reads files only
    through `files` and writes none.

    A missing directory is no problem when `settings.dir` is the default
    `.agents/wio/templates`, and holds no templates. Any other directory that is
    missing, is not a directory or is a symbolic link is an error, and nothing
    is walked. A file that cannot be read or decoded, a block that cannot be
    read, a `kind` that is missing or not a string, a `shape` or `description`
    that is not a string and a name that two files share are errors too, and the
    other templates are still found.

    Every diagnostic names its place as the file's path relative to `root`,
    written with `/` and followed by `:<line>` when the problem has a line, or as
    the directory's path. A duplicate name names both files, joined by `, `.

    Args:
        root: The repository root, which `settings.dir` and the templates' paths
            are relative to.
        settings: The `[templates]` table of the config, normalized and checked
            in its shape.
        files: The port that lists directories and reads files.

    Returns:
        The templates and the diagnostics.
    """
    directory = root / settings.dir
    refusal = refuse_directory(
        directory, settings.dir, files, noun="templates", default=_DEFAULT_DIR
    )
    if refusal is not None:
        return Discovery((), tuple(refusal))
    if not files.is_dir(directory):
        return Discovery((), ())
    built: list[Template] = []
    problems: list[Diagnostic] = []
    for path in walk_markdown(directory, files):
        found, diagnostics = _read(root, path, settings.kinds, files)
        built.extend(found)
        problems.extend(diagnostics)
    unique, repeats = _split_duplicates(built)
    ordered = sorted(unique, key=lambda template: template.name)
    return Discovery(tuple(ordered), sort_diagnostics([*problems, *repeats]))


def _read(
    root: Path, path: Path, kinds: Mapping[str, str], files: FileSystem
) -> tuple[list[Template], list[Diagnostic]]:
    """Read one file and build its template, if it is one.

    Args:
        root: The repository root.
        path: The file.
        kinds: The entry template of each declared kind.
        files: The port that reads the file.

    Returns:
        The template as a list of one, or none when the file is not a template
        or has a problem, and the problems found.
    """
    place = PurePosixPath(path.relative_to(root)).as_posix()
    try:
        block = read_metadata_block(files.read_text(path))
    except UnicodeDecodeError:
        return [], [_error(place, "The file is not valid UTF-8")]
    except OSError as error:
        return [], [_error(place, f"The file cannot be read: {error.strerror}")]
    except MetadataBlockError as error:
        return [], [_error(f"{place}:{error.line}", error.message)]
    if block is None:
        return [], []
    problems = _key_problems(place, block.data)
    if problems:
        return [], problems
    name = path.name.removesuffix(_SUFFIX)
    kind = str(block.data["kind"])
    template = Template(
        name=name,
        kind=kind,
        shape=_text(block.data, "shape"),
        description=_text(block.data, "description"),
        path=path.relative_to(root),
        entry=kinds.get(kind) == name,
    )
    return [template], []


def _key_problems(place: str, data: Mapping[str, object]) -> list[Diagnostic]:
    """Judge the keys a template needs to be built.

    Args:
        place: The file's place.
        data: The decoded metadata of the template.

    Returns:
        An error for a `kind` that is missing or not a string, and for a `shape`
        or `description` that is present and not a string.
    """
    problems: list[Diagnostic] = []
    if "kind" not in data:
        problems.append(_error(place, "A template needs a `kind`"))
    elif not isinstance(data["kind"], str):
        problems.append(_error(place, "`kind` must be a string"))
    problems.extend(
        _error(place, f"`{key}` must be a string")
        for key in ("shape", "description")
        if key in data and not isinstance(data[key], str)
    )
    return problems


def _text(data: Mapping[str, object], key: str) -> str | None:
    """Read an optional text key.

    Args:
        data: The decoded metadata.
        key: The key.

    Returns:
        The text, or `None` when the key is absent.
    """
    value = data.get(key)
    return value if isinstance(value, str) else None


def _split_duplicates(
    templates: list[Template],
) -> tuple[list[Template], list[Diagnostic]]:
    """Set aside the templates whose names are shared.

    Args:
        templates: The templates built.

    Returns:
        The templates with a unique name, and one error for each shared name
        that names every file with it.
    """
    by_name: dict[str, list[Template]] = {}
    for template in templates:
        by_name.setdefault(template.name, []).append(template)
    unique = [group[0] for group in by_name.values() if len(group) == 1]
    repeats = [
        _error(
            ", ".join(sorted(PurePosixPath(t.path).as_posix() for t in group)),
            f"Two templates are named `{name}`",
        )
        for name, group in by_name.items()
        if len(group) > 1
    ]
    return unique, repeats
