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
    """A section of a template: its text as written and its directives."""

    text: str
    directives: tuple[Directive, ...]


@dataclass(frozen=True)
class _Source:
    """What a template says about the body of a contract that follows it."""

    name: str
    sections: Mapping[str, _Section]


@dataclass(frozen=True)
class _Headings:
    """The `##` headings of a contract, by the section each one is."""

    firsts: Mapping[str, Heading]
    repeats: Sequence[tuple[Heading, int]]


@dataclass(frozen=True)
class _Directives:
    """The directives that apply to the sections of a contract, and the problems."""

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
        """Check one contract's `##` sections, directives, and item ids.

        Uses directives from `template` when the contract names one, or from
        the contract's own `##` headings otherwise. Returns no diagnostics when
        the named template is missing, rejected, or unreadable (reported by
        `wio templates check`), and caches template reads across calls.

        Args:
            work: The Work being checked.
            block: Its parsed metadata block and body.
            template: The catalog entry for `work.template`, or `None`.

        Returns:
            Unsorted diagnostics for missing required sections, unknown or
            repeated headings, ignored or invalid directives, and item ids.
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

    def items(self, block: MetadataBlock, template: Template | None) -> frozenset[str]:
        """Find the ids that the own sections of a contract carry.

        The sections are those of the contract, and the directives that give them
        ids are the template's `pattern` directives, found with `find_items` over
        the first section of each text, as `check` finds them. It judges nothing
        and reports nothing.

        Args:
            block: The contract's metadata block, whose body the ids are found in.
            template: The template the catalog gave for the Work, or `None` for a
                Work with none or with one that is missing or rejected.

        Returns:
            The ids, such as `AC-1`, empty for a contract with no template, a
            template that cannot be used, or no section that has a `pattern`.
        """
        source = None if template is None else self._source(template)
        if source is None:
            return frozenset()
        outline = read_outline(block.body, block.body_start_line)
        headings = _level_two(outline)
        by_key = _directives("", outline, headings, source).by_key
        return _pattern_ids(block, headings, by_key)

    def _source(self, template: Template) -> _Source | None:
        """Give what a template says, reading its file the first time."""
        if template.name not in self._read:
            self._read[template.name] = _read_template(
                template, self._root, self._files
            )
        return self._read[template.name]


def _read_template(template: Template, root: Path, files: FileSystem) -> _Source | None:
    """Read the sections of a template and their directives from its file."""
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
    """Split the `##` headings of a body into first ones and repeats."""
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
    """Choose the directives of each section, and judge the contract's own lists."""
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
    """Give the key that sections are matched by."""
    return _text_of(heading).casefold()


def _parsed(heading: Heading) -> tuple[Directive, ...]:
    """Read the directives of a heading, none for a list that the parser refuses."""
    try:
        parsed = read_directive_heading(heading.raw)
    except DirectiveSyntaxError:
        return ()
    return () if parsed is None else parsed.directives


def _list_problems(place: str, heading: Heading) -> list[Diagnostic]:
    """Judge the directive list of one heading of a contract with no template."""
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
    """Word the warning for a section that the template does not have."""
    message = f"The section `{text}` is not in the template `{template}`"
    return f"{message}. Did you mean `{close}`?" if close else message


def _title_warning(work: Work) -> list[Diagnostic]:
    """Warn of a contract that has no heading."""
    if work.title is not None:
        return []
    return [Diagnostic("warning", work.path.as_posix(), "The contract has no title")]


def _repeat_warnings(place: str, headings: _Headings) -> list[Diagnostic]:
    """Warn of each `##` heading that repeats an earlier one."""
    return [
        Diagnostic(
            "warning",
            f"{place}:{heading.line}",
            f"The section `{_text_of(heading)}` is repeated; the first one counts",
        )
        for heading, _first in headings.repeats
    ]


def _text_of(heading: Heading) -> str:
    """Give the text of a heading before a directive list, as written."""
    opener = _OPENER.search(heading.raw)
    before = heading.raw if opener is None else heading.raw[: opener.start()]
    return _CLOSING_MARKS.sub("", _LEADING_MARKS.sub("", before.strip())).strip()


def _against_template(
    place: str, outline: Sequence[Heading], headings: _Headings, source: _Source | None
) -> list[Diagnostic]:
    """Judge the contract's sections and lists against its template."""
    if source is None:
        return []
    return [
        *_section_findings(place, headings, source),
        *_ignored_lists(place, outline, source.name),
    ]


def _section_findings(
    place: str, headings: _Headings, source: _Source
) -> list[Diagnostic]:
    """Judge the contract's `##` sections against the template's."""
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
    """Warn of each directive list of a contract that follows a template."""
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
    """Find and judge the items of the sections that have `items` or `pattern`."""
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


def _pattern_ids(
    block: MetadataBlock,
    headings: _Headings,
    by_key: Mapping[str, tuple[Directive, ...]],
) -> frozenset[str]:
    """Find the ids of the sections that have a `pattern` directive."""
    sections = [
        (heading, by_key[key])
        for key, heading in headings.firsts.items()
        if _has_pattern(by_key.get(key, ()))
    ]
    ids = [
        item.id
        for heading, directives in sections
        for item in find_items(block.body, block.body_start_line, heading, directives)
    ]
    return frozenset(i for i in ids if i is not None)


def _has_pattern(directives: Sequence[Directive]) -> bool:
    """Tell whether a section's directives give its items an id."""
    return any(isinstance(d, Pattern) for d in directives)
