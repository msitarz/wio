# SPDX-License-Identifier: Apache-2.0
"""Checking every template of a project: what is wrong with them, all at once."""

import re
from dataclasses import dataclass
from functools import partial
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

from wio.formats.errors import DirectiveSyntaxError, MetadataBlockError
from wio.models.diagnostics import Diagnostic, order_diagnostics
from wio.templates.discovery import discover
lazy from wio.formats import (
    read_directive_heading,
    read_metadata_block,
    read_outline,
)

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
_OPENER = re.compile(r"<!--\s*wio:\s*")
"""The opener of a directive list, as the directive parser reads it."""
_LEADING_MARKS = re.compile(r"^#+\s*")
_CLOSING_MARKS = re.compile(r"\s+#+\s*$")
_KEYS = frozenset({"kind", "shape", "description", "actions", "contract"})
_TABLES = ("actions", "contract")

DIRECTIVE_LEVEL: HeadingLevel = 2
"""The only heading level on which a directive list is read."""

PASSES = "The templates pass."
"""What the command says when the check has no diagnostic to print."""


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
    names of those files, taken from the places of discovery's errors, and one
    whose second read failed is still in `check_kinds`' input, so it is judged
    as a template and not reported missing. A default templates directory that
    does not exist holds no templates, so each entry template is reported
    missing.

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
    judged = _judge(readings, found.templates, config, unbuilt)
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
    readings: list[Reading],
    templates: Iterable[Template],
    config: Config,
    unbuilt: Collection[str],
) -> Iterator[Diagnostic]:
    """Run every check on the templates that were read.

    Args:
        readings: The templates that could be read a second time.
        templates: Every template that discovery built, whether or not it could
            be read again, since the kinds check reads no file.
        config: The settings the templates are judged against.
        unbuilt: The names of the files that discovery could not build.

    Yields:
        The diagnostics of the checks, in no particular order.
    """
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
    problems: list[Diagnostic] = []
    for key in data:
        if key == "name":
            message = "A template has no `name` key: it is named by its file"
            problems.append(_error(place, message))
        elif key not in _KEYS:
            problems.append(_error(place, f"Unknown key `{key}` in the metadata"))
    problems.extend(
        _error(place, f"`{key}` must be a table")
        for key in _TABLES
        if key in data and not isinstance(data[key], dict)
    )
    return problems


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

        The text of a heading for the repeats is its text before the directive
        list, so a heading whose list is refused still counts. A heading that is
        not level 2 whose list is refused gets that one error, and a heading
        with no list gets none.
    """
    problems: list[Diagnostic] = []
    seen: dict[str, int] = {}
    for heading in reading.headings:
        problems.extend(_directive_problems(reading.place, heading, level))
        if heading.level == level:
            problems.extend(_repeat_problems(reading.place, heading, seen))
    return problems


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

        An `actions` that is not a table is the error of `check_keys`, so this
        returns nothing for it, and the one mistake is reported once.
    """
    if not isinstance(actions, dict):
        return []
    problems: list[Diagnostic] = []
    for action, value in actions.items():
        if action not in config.actions:
            problems.append(_error(place, f"The action `{action}` is not declared"))
        problems.extend(_value_problems(place, action, value, config))
    return problems


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
        from the one it starts. A template of an undeclared kind gets the first
        error only, even when it is also an entry template.
    """
    names = {template.name for template in templates}
    problems: list[Diagnostic] = []
    for template in templates:
        problems.extend(_kind_problems(template, kinds))
    for kind, entry in kinds.items():
        if entry not in names and entry not in unbuilt:
            message = f"The entry template `{entry}` of the kind `{kind}` is missing"
            problems.append(_error(f"templates.kinds.{kind}", message))
    return problems


def _directive_problems(
    place: str, heading: Heading, level: HeadingLevel
) -> list[Diagnostic]:
    """Judge the directive list of one heading.

    Args:
        place: The template's file.
        heading: The heading.
        level: The one level on which directives are read.

    Returns:
        The error of a list the parser refuses, or of a list on another level,
        or nothing.
    """
    where = f"{place}:{heading.line}"
    try:
        parsed = read_directive_heading(heading.raw)
    except DirectiveSyntaxError as error:
        return [_error(f"{where}:{error.column}", error.message)]
    if parsed is None or not parsed.directives or heading.level == level:
        return []
    opener = _OPENER.search(heading.raw)
    column = 1 if opener is None else opener.start() + 1
    message = f"Directives are read on level-{level} headings only"
    return [_error(f"{where}:{column}", message)]


def _repeat_problems(
    place: str, heading: Heading, seen: dict[str, int]
) -> list[Diagnostic]:
    """Judge whether a heading repeats an earlier one of the same template.

    Args:
        place: The template's file.
        heading: A heading of the level that is checked for repeats.
        seen: The line of the first heading with each text so far; this adds
            the heading when it is the first.

    Returns:
        A warning when an earlier heading has the same text, otherwise nothing.
    """
    text = _comparable(heading)
    if text not in seen:
        seen[text] = heading.line
        return []
    message = f"The heading repeats the one on line {seen[text]}"
    return [Diagnostic("warning", f"{place}:{heading.line}", message)]


def _comparable(heading: Heading) -> str:
    """Reduce a heading to the text that repeats are compared by.

    Args:
        heading: The heading.

    Returns:
        Its text before a directive list, without the `#` marks, the whitespace
        around it and the case.
    """
    opener = _OPENER.search(heading.raw)
    raw = heading.raw if opener is None else heading.raw[: opener.start()]
    text = _CLOSING_MARKS.sub("", _LEADING_MARKS.sub("", raw.strip()))
    return text.strip().casefold()


def _value_problems(
    place: str, action: str, value: object, config: Config
) -> list[Diagnostic]:
    """Judge the value of one entry of `[actions]`.

    Args:
        place: The template's file.
        action: The entry's key.
        value: Its value.
        config: The settings that declare the stage presets and the stages.

    Returns:
        An error for a name the config does not declare, or for a value that is
        neither a name nor a list of names.
    """
    match value:
        case str():
            return _undeclared(place, "stage preset", [value], config.stage_presets)
        case list() if all(isinstance(name, str) for name in value):
            return _undeclared(place, "stage", value, config.stages)
        case _:
            return [_error(place, f"`{action}` must be a name or a list of names")]


def _undeclared(
    place: str, noun: str, names: Iterable[str], declared: Mapping[str, object]
) -> list[Diagnostic]:
    """Make an error for each name that the config does not declare.

    Args:
        place: The template's file.
        noun: What the names are, such as `stage`.
        names: The names to look up.
        declared: The config's declarations of that kind, by name.

    Returns:
        An error for each name that is not a key of `declared`.
    """
    return [
        _error(place, f"The {noun} `{name}` is not declared")
        for name in names
        if name not in declared
    ]


def _kind_problems(template: Template, kinds: Mapping[str, str]) -> list[Diagnostic]:
    """Judge one template's kind against the declared kinds.

    Args:
        template: The template.
        kinds: The entry template of each declared kind.

    Returns:
        An error for a kind that is not declared, and one for an entry template
        of another kind than the one it starts.
    """
    place = PurePosixPath(template.path).as_posix()
    if template.kind not in kinds:
        message = f"The kind `{template.kind}` is not declared in `[templates.kinds]`"
        return [_error(place, message)]
    started = [kind for kind, entry in kinds.items() if entry == template.name]
    if started and template.kind not in started:
        message = (
            f"The template is the entry template of `{started[0]}`, but its kind "
            f"`{template.kind}` differs from it"
        )
        return [_error(place, message)]
    return []
