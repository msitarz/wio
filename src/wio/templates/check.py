# SPDX-License-Identifier: Apache-2.0
"""Checking every template of a project: what is wrong with them, all at once."""

import re
from dataclasses import dataclass
from functools import partial
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from wio.formats.errors import MetadataBlockError
from wio.models.diagnostics import Diagnostic
from wio.templates.discovery import discover
lazy from wio.formats import read_metadata_block, read_outline

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Iterator, Mapping
    from pathlib import Path

    from wio.io.ports import FileSystem
    from wio.models.config import Config, Templates
    from wio.models.heading import Heading, HeadingLevel
    from wio.models.template import Template
    from wio.templates.discovery import Discovery

_error = partial(Diagnostic, "error")
"""Make an error diagnostic from a place and a message."""
_POSITION = re.compile(r"(:\d+)+$")
"""The `:<line>` and `:<column>` that end a place."""

DIRECTIVE_LEVEL: HeadingLevel = 2
"""The only heading level on which a directive list is read."""

PASSES = "The templates pass."
"""What `render_check` says when there is no diagnostic to print."""


@dataclass(frozen=True)
class Reading:
    """One template read for the check: what it is, where, and what it says.

    It is immutable. It is read after discovery, so the template is one that
    discovery could build.

    Attributes:
        template: The template that discovery built.
        place: The file's path relative to the repository root, written with
            `/`, which every diagnostic of the file starts with.
        data: The decoded metadata block, as the block reader returns it.
        headings: The real headings of the body, in the order they appear, each
            with its line in the file.
    """

    template: Template
    place: str
    data: dict[str, object]
    headings: tuple[Heading, ...]


def check_templates(
    root: Path, config: Config, files: FileSystem
) -> tuple[Diagnostic, ...]:
    """Find every problem of the templates of a project.

    It walks the templates directory with `discover`, reads each template that
    discovery built, and runs the checks below on all of them, so a problem in
    one template never hides another. It reads files only through `files` and
    writes none. The diagnostics of `discover` are errors of the check as they
    are. A templates directory that discovery refuses, because it is missing,
    is not a directory or is a symbolic link, is that one error: the check
    returns it alone and runs nothing else, so no entry template is reported
    missing because of it. An entry template whose file discovery reported an
    error is not reported missing either: the check passes `check_kinds` the
    names of those files, taken from the places of discovery's errors.

    Args:
        root: The repository root, which `config.templates.dir` and the
            templates' paths are relative to.
        config: The settings, whose declared actions, stage presets, stages and
            kinds the templates are judged against.
        files: The port that lists directories and reads files.

    Returns:
        Every diagnostic, in the order of `order_diagnostics`; empty when the
        templates pass. A file that cannot be read a second time is one error
        for the file, worded as discovery words it.
    """
    found = discover(root, config.templates, files)
    if _directory_refused(found, config.templates):
        return order_diagnostics(found.diagnostics)
    readings: list[Reading] = []
    problems: list[Diagnostic] = []
    for template in found.templates:
        read = _read(root, template, files)
        if isinstance(read, Diagnostic):
            problems.append(read)
        else:
            readings.append(read)
    unbuilt = _unbuilt_names(found.diagnostics)
    judged = _judge(readings, config, unbuilt)
    return order_diagnostics([*found.diagnostics, *problems, *judged])


def _directory_refused(found: Discovery, settings: Templates) -> bool:
    """Tell whether discovery refused the templates directory itself.

    Args:
        found: What the walk found.
        settings: The `[templates]` table of the config.

    Returns:
        Whether the walk built nothing and reported an error whose place is the
        directory, which is how it reports a directory that it cannot walk.
    """
    return not found.templates and any(
        diagnostic.where == settings.dir for diagnostic in found.diagnostics
    )


def _unbuilt_names(diagnostics: Iterable[Diagnostic]) -> frozenset[str]:
    """Name the templates whose files discovery reported an error for.

    Args:
        diagnostics: The diagnostics of discovery.

    Returns:
        The file names without `.md` of the places that end in `.md`, once the
        `:<line>` of a place and the `, ` that joins the files of a duplicate are
        taken off.
    """
    places = (
        _POSITION.sub("", part)
        for diagnostic in diagnostics
        for part in diagnostic.where.split(", ")
    )
    return frozenset(
        PurePosixPath(place).name.removesuffix(".md")
        for place in places
        if place.endswith(".md")
    )


def _read(root: Path, template: Template, files: FileSystem) -> Reading | Diagnostic:
    """Read a template that discovery built, a second time, for its headings.

    Args:
        root: The repository root.
        template: The template.
        files: The port that reads the file.

    Returns:
        The reading, or the one error for the file, worded as discovery words
        it, when it cannot be read now.
    """
    place = PurePosixPath(template.path).as_posix()
    try:
        block = read_metadata_block(files.read_text(root / template.path))
    except UnicodeDecodeError:
        return _error(place, "The file is not valid UTF-8")
    except OSError as error:
        return _error(place, f"The file cannot be read: {error.strerror}")
    except MetadataBlockError as error:
        return _error(f"{place}:{error.line}", error.message)
    if block is None:
        return _error(place, "The file is not a template")
    headings = read_outline(block.body, block.body_start_line)
    return Reading(template, place, block.data, headings)


def _judge(
    readings: list[Reading], config: Config, unbuilt: Collection[str]
) -> Iterator[Diagnostic]:
    """Run every check on the templates that were read.

    Args:
        readings: The templates, read.
        config: The settings the templates are judged against.
        unbuilt: The names of the files that discovery could not build.

    Yields:
        The diagnostics of the checks, in no particular order.
    """
    templates = [reading.template for reading in readings]
    yield from check_kinds(templates, config.templates.kinds, unbuilt)
    for reading in readings:
        yield from check_keys(reading.place, reading.data)
        yield from check_headings(reading)
        actions = reading.data.get("actions", {})
        yield from check_actions(reading.place, actions, config)


def check_keys(place: str, data: Mapping[str, object]) -> list[Diagnostic]:
    """Judge the keys of one template's metadata.

    Args:
        place: The template's file, as `Reading.place` words it.
        data: The decoded metadata block.

    Returns:
        An error naming the file and the key for each key outside `kind`,
        `shape`, `description`, `actions` and `contract`, the one for `name`
        saying that a template is named by its file, and for an `actions` or a
        `contract` that is not a table. The keys under `contract` are free.
    """
    raise NotImplementedError


def check_headings(
    reading: Reading, *, level: HeadingLevel = DIRECTIVE_LEVEL
) -> list[Diagnostic]:
    """Judge the headings of one template: their directive lists and repeats.

    Args:
        reading: The template, read.
        level: The one heading level on which directives are read.

    Returns:
        An error for each heading whose directive list the parser refuses, a
        list that does not close on its line included, whose place is
        `<file>:<line>:<column>` with the parser's column; an error for a list
        on a heading that is not level 2, saying that directives are read on
        level-2 headings only, whose column is that of the list's opener; and a
        warning for each level-2 heading whose text, ignoring case, the
        whitespace around it and a trailing directive list, was seen on an
        earlier heading, whose place is the file and the line of the later
        heading and whose message names the line of the first.

        The text of a heading for the repeats is its raw line without the
        directive list, which `remove_directive_list` of `wio.formats` gives, so
        a heading whose list is refused still counts, by the text before the
        list. A heading that is not level 2 whose list is refused gets that one
        error, and a heading with no list gets none.
    """
    raise NotImplementedError


def check_actions(place: str, actions: object, config: Config) -> list[Diagnostic]:
    """Judge the names in one template's `[actions]` against the config.

    A key of `[actions]` names an action, and its value names a stage preset or
    stages, as one string or a list of strings. A name is judged only by whether
    the config declares it, and never by whether the pipeline makes sense.

    Args:
        place: The template's file, as `Reading.place` words it.
        actions: The `actions` key of its metadata, which may be of any type.
        config: The settings that declare the actions, the stage presets and the
            stages.

    Returns:
        An error naming the file and the name for an action, a stage preset or a
        stage that the config does not declare, and an error naming the file and
        the key for a value that is neither a string nor a list of strings. An
        empty list is no error.
    """
    raise NotImplementedError


def check_kinds(
    templates: Iterable[Template],
    kinds: Mapping[str, str],
    unbuilt: Collection[str] = (),
) -> list[Diagnostic]:
    """Judge the templates' kinds and the entry templates against the config.

    Args:
        templates: The templates that discovery built.
        kinds: `[templates.kinds]` of the config: the entry template of each
            declared kind.
        unbuilt: The names of the template files that discovery could not build
            because of an error of their own. An entry template among them is
            not missing, and is not reported as such.

    Returns:
        An error naming the file and the kind for a template whose kind is not
        declared, an error whose place is the key path `templates.kinds.<kind>`
        and that names the entry for an entry template that does not exist, and
        an error naming the file for an entry template whose own kind differs
        from the one it starts.
    """
    raise NotImplementedError


def order_diagnostics(diagnostics: Iterable[Diagnostic]) -> tuple[Diagnostic, ...]:
    """Put the diagnostics of the check in the order it prints them.

    This is not `sort_diagnostics`, which compares `where` as a plain string.

    Args:
        diagnostics: The findings, in any order.

    Returns:
        The findings sorted by file, line and column, the numbers compared as
        numbers so that line 4 comes before line 12. A place is read as a file, an
        optional line and an optional column; a file without a line comes before
        its lines. A place that is not of that form, such as a key path or the
        two files of a duplicate name joined by `, `, is compared as its text,
        and all of the places of that form come before it. Ties are broken by
        error, warning and note, then by message.
    """
    raise NotImplementedError


def render_check(diagnostics: Iterable[Diagnostic], *, as_json: bool) -> str:
    """Render what the check found, in the order given.

    Args:
        diagnostics: The findings, already in the order of `order_diagnostics`.
        as_json: Whether to write the JSON array instead of the text.

    Returns:
        With `as_json`, the array of `severity`, `where` and `message` objects,
        `[]` for none, ending in a newline. Otherwise `PASSES` and a newline
        when there is no diagnostic, and the `<severity>: <where>: <message>`
        lines when there are some, each ending in a newline.
    """
    raise NotImplementedError
