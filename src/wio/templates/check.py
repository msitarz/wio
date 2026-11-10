# SPDX-License-Identifier: Apache-2.0
"""Checking every template of a project: what is wrong with them, all at once."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from wio.io.ports import FileSystem
    from wio.models.config import Config
    from wio.models.diagnostics import Diagnostic
    from wio.models.heading import Heading, HeadingLevel
    from wio.models.template import Template

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
    are. A templates directory that is missing or invalid is that one error, and
    no check that follows reports an entry template missing because of it.

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
    raise NotImplementedError


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
    templates: Iterable[Template], kinds: Mapping[str, str]
) -> list[Diagnostic]:
    """Judge the templates' kinds and the entry templates against the config.

    Args:
        templates: The templates that discovery built.
        kinds: `[templates.kinds]` of the config: the entry template of each
            declared kind.

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
        numbers so that line 4 comes before line 12; a place without a line or a
        column, and a key path, come in the order of their text; then error,
        warning and note, then message.
    """
    raise NotImplementedError


def render_check(diagnostics: Iterable[Diagnostic], *, as_json: bool) -> str:
    """Render what the check found, in the order given.

    Args:
        diagnostics: The findings, already in the order of `order_diagnostics`.
        as_json: Whether to write the JSON array instead of the text.

    Returns:
        With `as_json`, the array of `severity`, `where` and `message` objects,
        `[]` for none. Otherwise `PASSES` and a newline when there is no
        diagnostic, and the `<severity>: <where>: <message>` lines when there
        are some, each ending in a newline.
    """
    raise NotImplementedError
