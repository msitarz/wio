# SPDX-License-Identifier: Apache-2.0
"""What `wio contracts check` reports about the body of a contract."""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from wio.formats.errors import DirectiveSyntaxError, MetadataBlockError
from wio.models.diagnostics import Diagnostic
from wio.models.directives import Items, Pattern, Required
from wio.models.item import SectionItems
lazy from wio.formats import (
    closest_key,
    find_items,
    judge_items,
    read_directive_heading,
    read_metadata_block,
    read_outline,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from wio.io.ports import FileSystem
    from wio.models.block import MetadataBlock
    from wio.models.directives import Directive
    from wio.models.heading import Heading
    from wio.models.template import Template
    from wio.models.works import Work


_OPENER: Final = re.compile(r"<!--\s*wio:\s*")
"""The opener of a directive list, as the directive parser reads it."""
_LEVEL: Final = 2
"""The one heading level whose sections carry directives."""
_LEADING_MARKS: Final = re.compile(r"^#+\s*")
_CLOSING_MARKS: Final = re.compile(r"\s+#+\s*$")


@dataclass(frozen=True)
class _Section:
    """A section of a template: its text as written and its directives.

    Attributes:
        text: The heading's text before a directive list, as the template writes
            it, which a message names it by.
        directives: The directives of the list on the heading.
    """

    text: str
    directives: tuple[Directive, ...]


@dataclass(frozen=True)
class _Source:
    """What a template says about the body of a contract that follows it.

    Attributes:
        name: The template's name.
        sections: Its `##` sections, each under the key that sections are matched
            by, the first of a repeated text only, in the order of the template.
    """

    name: str
    sections: Mapping[str, _Section]


@dataclass(frozen=True)
class _Headings:
    """The `##` headings of a contract, by the section each one is.

    Attributes:
        firsts: The first heading of each text, under the key that sections are
            matched by, in the order of the body.
        repeats: Each later heading of a text, with the line of the first.
    """

    firsts: Mapping[str, Heading]
    repeats: Sequence[tuple[Heading, int]]


@dataclass(frozen=True)
class _Directives:
    """The directives that apply to the sections of a contract, and the problems.

    Attributes:
        by_key: The directives of each section that the contract has, under the
            key that sections are matched by: the template's, or the contract's
            own when it names no template.
        problems: The errors of the contract's own lists that the parser refuses
            or that are on a heading that is not level 2, empty with a template.
    """

    by_key: Mapping[str, tuple[Directive, ...]]
    problems: list[Diagnostic]


class BodyChecker:
    """Checks the body of each contract against its source of directives.

    One checker serves one run of the check. It reads the file of a template once
    and shares what it found with every contract that follows the template, and
    it reads nothing else than through `files`, and writes nothing.
    """

    def __init__(self, root: Path, files: FileSystem) -> None:
        """Keep what a read of a template needs, and start with none made.

        Args:
            root: The repository root, which a template's `path` is relative to.
            files: The port that reads a template's file.
        """
        self._root = root
        self._files = files
        self._read: dict[str, _Source | None] = {}

    def check(
        self, work: Work, block: MetadataBlock, template: Template | None
    ) -> list[Diagnostic]:
        """Check the body of one contract.

        The source of directives is the template that the contract names, and
        only that: `work.template` names none, and then the source is the
        contract's own `##` headings and only those, and `template` is `None`; or
        it names one and `template` is what the catalog gave for it. A contract
        that names a template that is missing or rejected, which is `template`
        `None` with `work.template` set, gets no diagnostic at all, because the
        check of the Works has reported it. A template whose file cannot be read
        or decoded, whose block cannot be parsed or is missing, is skipped the
        same way, because `wio templates check` reports it, and the failed read is
        remembered so that it is not retried for the next contract. A Work whose
        `template` discovery reported as being of a wrong type has `work.template`
        `None` too, so it would read as one that names none: the caller, which
        already knows the fields that discovery reported, does not call this for
        it, and `_check_work` in `checking.py` does, with one shared checker for the
        run. A section is a `##` heading and what follows it up to the next
        heading of level 1 or 2, and sections deeper than level 2 are free.

        A `##` heading of the contract matches one of the template by its text,
        ignoring case, the whitespace around it and a trailing directive list,
        and nothing else is normalized. When a `##` heading is repeated, in the
        contract or in the template, the first is the section. A directive list is
        anything that begins with the opener `<!-- wio:`, which the parser reads as
        `<!--`, whitespace, `wio:` and whitespace, and the heading's text for
        matching is what comes before it. A heading whose list the parser refuses
        has a text too, so it is taken from the heading's line by an expression of
        this module and not from the parser, which raises for such a line.

        With a template:

        - A section that the template marks `required` and the contract lacks is
          an error at the file, ``The section `Goals` is required by the template
          `t` ``, named as the template writes it.
        - A directive list in the contract, on a heading of any level and whatever
          its syntax, changes nothing and is a warning at `<file>:<line>` of the
          heading, one for each list, ``The directive list is ignored because the
          contract follows the template `t` ``, and the parser's errors are not
          reported.
        - A `##` heading that the template does not have is a warning at its line,
          ``The section `Constraint` is not in the template `t` ``, with ``. Did
          you mean `Constraints`?`` when `closest_key` finds one among the texts of
          the template's sections as written.

        A directive list on a repeated heading gets both the warning that it is
        ignored and the warning that the heading is repeated. A template section
        that is `inherit` and `required` is still required, although the sections
        that a contract inherits are not checked.

        Without a template, the directives are those of the contract's own `##`
        headings. A list that the parser refuses is an error at
        `<file>:<line>:<column>` with the parser's column, and a list on a heading
        that is not level 2 is an error at the column of its opener, ``Directives
        are read on level-2 headings only``, on a repeated heading as on any
        other, because every list is judged.

        In both cases the items of each section that has `items` or `pattern`
        directives are found and judged with `find_items` and `judge_items`, over
        the first section of each text only, which are counted and whose ids are
        checked. A repeated `##` heading is a warning at its line, ``The section
        `Goals` is repeated; the first one counts``, and carries no items. A
        contract with no title, which is `work.title` `None`, is a warning at the
        file, ``The contract has no title``. The sections that a contract inherits
        are not checked.

        Args:
            work: The Work, for its file and its title.
            block: Its metadata block, read again, whose body is checked and whose
                `body_start_line` gives each heading its line in the file.
            template: The template the catalog gave for `work.template`, or `None`
                when the Work names none or names one that is missing or rejected.

        Returns:
            The findings in any order, none for a contract whose template is
            missing, rejected or unreadable.
        """
        source = None
        if work.template is not None:
            source = self._source(template) if template is not None else None
            if source is None:
                return []
        place = work.path.as_posix()
        outline = read_outline(block.body, block.body_start_line)
        headings = _level_two(outline)
        directives = _directives(place, outline, headings, source)
        return [
            *_title_warning(work),
            *_repeat_warnings(place, headings),
            *_against_template(place, outline, headings, source),
            *directives.problems,
            *_item_errors(place, block, headings, directives.by_key),
        ]

    def _source(self, template: Template) -> _Source | None:
        """Give what a template says, reading its file the first time.

        Args:
            template: The template.

        Returns:
            What `_read_template` gave for it, which is `None` for a template
            that cannot be used, the same for every contract that follows it.
        """
        if template.name not in self._read:
            self._read[template.name] = _read_template(
                template, self._root, self._files
            )
        return self._read[template.name]


def _read_template(template: Template, root: Path, files: FileSystem) -> _Source | None:
    """Read the sections of a template and their directives from its file.

    Args:
        template: The template, whose `path` is relative to the root.
        root: The repository root.
        files: The port that reads the file.

    Returns:
        The sections of its `##` headings, the first of a repeated text only, or
        `None` when the file cannot be read or decoded, its block cannot be
        parsed or is missing. A list that the parser refuses gives that section no
        directives, because `wio templates check` reports it.
    """
    try:
        block = read_metadata_block(files.read_text(root / template.path))
    except UnicodeDecodeError, OSError, MetadataBlockError:
        return None
    if block is None:
        return None
    sections: dict[str, _Section] = {}
    for heading in read_outline(block.body, block.body_start_line):
        key = _key(heading)
        if heading.level == _LEVEL and key not in sections:
            sections[key] = _Section(_text_of(heading), _parsed(heading))
    return _Source(template.name, sections)


def _level_two(outline: Sequence[Heading]) -> _Headings:
    """Split the `##` headings of a body into first ones and repeats.

    Args:
        outline: The real headings of the body, in order, of every level.

    Returns:
        The `##` headings by the key of their text, ignoring case, the whitespace
        around it and a trailing directive list, with each repeat and the line of
        the first.
    """
    firsts: dict[str, Heading] = {}
    repeats: list[tuple[Heading, int]] = []
    for heading in outline:
        key = _key(heading)
        if heading.level != _LEVEL:
            continue
        if key in firsts:
            repeats.append((heading, firsts[key].line))
        else:
            firsts[key] = heading
    return _Headings(firsts, repeats)


def _directives(
    place: str, outline: Sequence[Heading], headings: _Headings, source: _Source | None
) -> _Directives:
    """Choose the directives of each section, and judge the contract's own lists.

    Args:
        place: The contract's file.
        outline: The real headings of the body.
        headings: The `##` headings.
        source: What the template says, or `None` for a contract with none.

    Returns:
        The template's directives for each section that the contract has, or the
        lists of the contract's own first `##` headings, and with no template the
        parser's errors and the errors for a list on another level.
    """
    if source is not None:
        by_key = {
            key: source.sections[key].directives
            for key in headings.firsts
            if key in source.sections
        }
        return _Directives(by_key, [])
    problems = [
        problem for heading in outline for problem in _list_problems(place, heading)
    ]
    by_key = {key: _parsed(heading) for key, heading in headings.firsts.items()}
    return _Directives(by_key, problems)


def _key(heading: Heading) -> str:
    """Give the key that sections are matched by.

    Args:
        heading: A heading.

    Returns:
        Its text before a directive list, without the whitespace around it, in
        lowercase for comparison, and nothing else normalized.
    """
    return _text_of(heading).casefold()


def _parsed(heading: Heading) -> tuple[Directive, ...]:
    """Read the directives of a heading, none for a list that the parser refuses.

    Args:
        heading: A heading of a template or of a contract.

    Returns:
        The directives in the order written.
    """
    try:
        parsed = read_directive_heading(heading.raw)
    except DirectiveSyntaxError:
        return ()
    return () if parsed is None else parsed.directives


def _list_problems(place: str, heading: Heading) -> list[Diagnostic]:
    """Judge the directive list of one heading of a contract with no template.

    Args:
        place: The contract's file.
        heading: A heading of any level.

    Returns:
        The error of a list that the parser refuses, at its line and column, or of
        a list on a heading that is not level 2, at the column of its opener.
    """
    where = f"{place}:{heading.line}"
    try:
        parsed = read_directive_heading(heading.raw)
    except DirectiveSyntaxError as error:
        return [Diagnostic("error", f"{where}:{error.column}", error.message)]
    opener = _OPENER.search(heading.raw)
    if parsed is None or not parsed.directives or heading.level == _LEVEL:
        return []
    column = 1 if opener is None else opener.start() + 1
    message = f"Directives are read on level-{_LEVEL} headings only"
    return [Diagnostic("error", f"{where}:{column}", message)]


def _stray(text: str, template: str, close: str | None) -> str:
    """Word the warning for a section that the template does not have.

    Args:
        text: The section's text as written.
        template: The template's name.
        close: The closest section of the template, or `None`.

    Returns:
        The message, with the suggestion when there is one.
    """
    message = f"The section `{text}` is not in the template `{template}`"
    return f"{message}. Did you mean `{close}`?" if close else message


def _title_warning(work: Work) -> list[Diagnostic]:
    """Warn of a contract that has no heading.

    Args:
        work: The Work, whose `title` is the text of its first heading.

    Returns:
        ``The contract has no title`` as a warning at the file, or an empty list.
    """
    if work.title is not None:
        return []
    return [Diagnostic("warning", work.path.as_posix(), "The contract has no title")]


def _repeat_warnings(place: str, headings: _Headings) -> list[Diagnostic]:
    """Warn of each `##` heading that repeats an earlier one.

    Args:
        place: The contract's file.
        headings: The `##` headings.

    Returns:
        One warning at each repeat's line that names the section and says that
        the first one counts.
    """
    return [
        Diagnostic(
            "warning",
            f"{place}:{heading.line}",
            f"The section `{_text_of(heading)}` is repeated; the first one counts",
        )
        for heading, _first in headings.repeats
    ]


def _text_of(heading: Heading) -> str:
    """Give the text of a heading before a directive list, as written.

    It is taken from the line by an expression and not by the parser, which raises
    for a list that it refuses, so a heading whose list is refused has a text too.

    Args:
        heading: The heading.

    Returns:
        The line without its `#` marks, a closing sequence of them, the spaces
        around it, and a directive list and what follows it.
    """
    opener = _OPENER.search(heading.raw)
    before = heading.raw if opener is None else heading.raw[: opener.start()]
    return _CLOSING_MARKS.sub("", _LEADING_MARKS.sub("", before.strip())).strip()


def _against_template(
    place: str, outline: Sequence[Heading], headings: _Headings, source: _Source | None
) -> list[Diagnostic]:
    """Judge the contract's sections and lists against its template.

    Args:
        place: The contract's file.
        outline: The real headings of the body, whose lists are ignored.
        headings: The `##` headings.
        source: What the template says, or `None` for a contract with none, which
            gives nothing.

    Returns:
        The findings about the sections and the ignored lists.
    """
    if source is None:
        return []
    return [
        *_section_findings(place, headings, source),
        *_ignored_lists(place, outline, source.name),
    ]


def _section_findings(
    place: str, headings: _Headings, source: _Source
) -> list[Diagnostic]:
    """Judge the contract's `##` sections against the template's.

    Args:
        place: The contract's file.
        headings: The `##` headings of the contract, of which the first of each
            text is judged.
        source: What the template says.

    Returns:
        An error at the file for each section that the template requires and the
        contract lacks, ``The section `Goals` is required by the template `t` ``,
        named as the template writes it, in the template's order, and a warning at
        the line of each heading that the template does not have, ``The section
        `Constraint` is not in the template `t` ``, with ``. Did you mean
        `Constraints`?`` for the closest section by `closest_key` on the texts as
        written.
    """
    found = [
        Diagnostic(
            "error",
            place,
            f"The section `{section.text}` is required by the template `{source.name}`",
        )
        for key, section in source.sections.items()
        if Required() in section.directives and key not in headings.firsts
    ]
    texts = [section.text for section in source.sections.values()]
    found.extend(
        Diagnostic(
            "warning",
            f"{place}:{heading.line}",
            _stray(
                _text_of(heading), source.name, closest_key(_text_of(heading), texts)
            ),
        )
        for key, heading in headings.firsts.items()
        if key not in source.sections
    )
    return found


def _ignored_lists(
    place: str, outline: Sequence[Heading], template: str
) -> list[Diagnostic]:
    """Warn of each directive list of a contract that follows a template.

    Args:
        place: The contract's file.
        outline: The real headings of the body, of every level.
        template: The template's name.

    Returns:
        One warning at the line of the heading for each list, however it is
        written, saying that it is ignored because the contract follows the
        template.
    """
    message = (
        "The directive list is ignored because the contract follows the template "
        f"`{template}`"
    )
    return [
        Diagnostic("warning", f"{place}:{heading.line}", message)
        for heading in outline
        for _ in _OPENER.finditer(heading.raw)
    ]


def _item_errors(
    place: str,
    block: MetadataBlock,
    headings: _Headings,
    by_key: Mapping[str, tuple[Directive, ...]],
) -> list[Diagnostic]:
    """Find and judge the items of the sections that have `items` or `pattern`.

    Args:
        place: The contract's file.
        block: The block, whose body and first line the items are found in.
        headings: The `##` headings, of which only the first of each text counts.
        by_key: The directives of each section.

    Returns:
        What `judge_items` finds for the sections, over the first heading of each
        text only.
    """
    sections = [
        SectionItems(
            heading,
            by_key[key],
            find_items(block.body, block.body_start_line, heading, by_key[key]),
        )
        for key, heading in headings.firsts.items()
        if any(isinstance(d, Items | Pattern) for d in by_key.get(key, ()))
    ]
    return list(judge_items(place, sections))
