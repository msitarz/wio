# SPDX-License-Identifier: Apache-2.0
"""The resolved view of a Work: its contract and what its ancestors pass on."""

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from wio.formats.errors import DirectiveSyntaxError, MetadataBlockError
from wio.models.directives import Inherit
lazy from wio.formats import (
    read_directive_heading,
    read_metadata_block,
    read_outline,
    remove_directive_list,
)
lazy from wio.models.resolved import InheritedSections, ResolvedContract

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from wio.contracts.ports import TemplateCatalog
    from wio.io.ports import FileSystem
    from wio.models.heading import Heading
    from wio.models.works import Work

_LEVEL: Final = 2
"""The one heading level whose sections inherit."""
_DEEPEST: Final = 6
"""The deepest heading level, which a demotion does not pass."""
_MARKS: Final = re.compile(r"#{1,6}\s+")
_COMMENT: Final = re.compile(r"<!--.*?-->", re.DOTALL)
_CLOSING: Final = re.compile(r"\s+#+$")
"""The closing sequence of an ATX heading, which is not part of its text."""


@dataclass(frozen=True)
class _Body:
    """The body of a file as lines, and the real headings in it.

    Attributes:
        lines: The body's lines, split at CRLF, CR and LF alike, so none ends in
            a carriage return.
        headings: The real headings of the body, whose `line` counts from 1 in
            `lines`.
    """

    lines: tuple[str, ...]
    headings: tuple[Heading, ...]


def resolve_work(
    work: Work,
    ancestors: Sequence[Work],
    catalog: TemplateCatalog,
    root: Path,
    files: FileSystem,
) -> ResolvedContract:
    """Resolve a Work against its ancestors.

    It reads through `files` and writes nothing, and the same files give the same
    value. The Work's own contract is cleaned by `_own_contract`, and each
    ancestor passes what `_marked_texts` and `_cut_ancestor` say. An ancestor
    that cannot be used passes nothing, without an error, and the walk goes on to
    the ancestors above it.

    Args:
        work: The Work to resolve, whose contract is read from `root / work.path`.
        ancestors: Its ancestors, nearest first, as the hierarchy gives them,
            empty for a Work without a parent and under `flat`.
        catalog: Finds an ancestor's template and says whether it is rejected.
        root: The repository root, which a Work's and a template's `path` are
            relative to.
        files: The port that reads the files.

    Returns:
        The Work's own contract and, for each ancestor that passes anything, its
        sections, nearest ancestor first.

    Raises:
        OSError: The Work's own file cannot be read.
        UnicodeDecodeError: The Work's own file is not UTF-8.
        ConfigurationError: The config cannot be loaded, which `catalog` raises.
    """
    own = _own_contract(files.read_text(root / work.path))
    found = (_inherited(a, catalog, root, files) for a in ancestors)
    return ResolvedContract(work, own, tuple(i for i in found if i is not None))


def render_resolved(resolved: ResolvedContract) -> str:
    """Render the resolved view as one text.

    It reads nothing and writes nothing, and its output is deterministic: LF line
    endings and the same bytes for the same value. The layout is the Work's own
    contract first, then for each entry of `inherited`, in order, one blank line,
    the line `## Inherited from: <title> (<id>)`, one blank line, and the entry's
    sections with one blank line between them. A view that begins with an empty
    own contract starts with the first `## Inherited from:` line, with no blank
    line before it.

    Args:
        resolved: The parts of a Work's view.

    Returns:
        The text, ending in one line ending, and the empty string when the own
        contract is empty and nothing is inherited.
    """
    parts = [resolved.own]
    for entry in resolved.inherited:
        header = f"## Inherited from: {entry.title} ({entry.ancestor.id})"
        parts.extend((header, *entry.sections))
    text = "\n\n".join(part for part in parts if part)
    return f"{text}\n" if text else ""


def _inherited(
    ancestor: Work, catalog: TemplateCatalog, root: Path, files: FileSystem
) -> InheritedSections | None:
    """Gather what one ancestor passes on.

    Args:
        ancestor: The ancestor.
        catalog: Finds the ancestor's template and says whether it is rejected.
        root: The repository root that paths are relative to.
        files: The port that reads the files.

    Returns:
        Its title and sections, or `None` when it passes nothing: its file cannot
        be read, its source of directives cannot be used, or no section passes.
    """
    try:
        text = files.read_text(root / ancestor.path)
    except OSError, UnicodeDecodeError:
        return None
    marked = _marked_texts(ancestor, text, catalog, root, files)
    title, sections = ("", ()) if marked is None else _cut_ancestor(text, marked)
    return InheritedSections(ancestor, title, sections) if sections else None


def _own_contract(text: str) -> str:
    """Take a Work's file down to its own contract as the view starts.

    Args:
        text: The whole file.

    Returns:
        The text after the metadata block, with LF endings, comments kept, a
        readable directive list taken off every real heading and the blank lines
        at either end removed. A file without a readable block has none.
    """
    body = _read_body(text)
    if body is None:
        return ""
    lines = list(body.lines)
    for heading in body.headings:
        lines[heading.line - 1] = _clean(heading.raw)
    return "\n".join(_trim(lines))


def _marked_texts(
    ancestor: Work,
    text: str,
    catalog: TemplateCatalog,
    root: Path,
    files: FileSystem,
) -> frozenset[str] | None:
    """Find the `##` sections that an ancestor's source of directives marks.

    A failed read of the template's file, an `OSError` or a `UnicodeDecodeError`
    of `files`, and a template whose block cannot be read, are swallowed here and
    give `None`, because the ancestor then passes nothing.

    Args:
        ancestor: The ancestor, whose `template` names its source.
        text: The ancestor's whole file, the source when it names no template.
        catalog: Finds the template and says whether it is rejected.
        root: The repository root that the template's path is relative to.
        files: The port that reads the template's file.

    Returns:
        The text of each marked section as sections are matched, which is
        lowercase, without the whitespace around it and without a trailing
        directive list; empty when a readable list marks nothing; and `None` when
        the template is missing, rejected or cannot be read.
    """
    if ancestor.template is None:
        return _marked_in(text)
    template = catalog.find(ancestor.template)
    if template is None or catalog.is_rejected(ancestor.template):
        return None
    try:
        source = files.read_text(root / template.path)
    except OSError, UnicodeDecodeError:
        return None
    return _marked_in(source)


def _cut_ancestor(text: str, marked: frozenset[str]) -> tuple[str, tuple[str, ...]]:
    """Name an ancestor and cut the sections of it that pass, from one outline.

    Args:
        text: The ancestor's whole file.
        marked: The matching text of each marked section.

    Returns:
        The ancestor's title, which is the text of its first real heading at any
        level with a readable directive list taken off, and each level-2 section
        whose text matches, in the ancestor's order, as its heading line demoted
        by one level, never below 6, and its text, without the blank lines that
        end it. A section with only comments and whitespace is left out.
    """
    body = _read_body(text)
    if body is None or not body.headings:
        return "", ()
    sections = (
        _section(body, index)
        for index, heading in enumerate(body.headings)
        if heading.level == _LEVEL and _key(heading.raw) in marked
    )
    return _title(body.headings[0]), tuple(s for s in sections if s)


def _read_body(text: str) -> _Body | None:
    """Split a file into the lines of its body and the real headings.

    Args:
        text: The whole file.

    Returns:
        The body, or `None` for a file without a metadata block or with one that
        cannot be read.
    """
    try:
        block = read_metadata_block(text)
    except MetadataBlockError:
        return None
    if block is None:
        return None
    lines = tuple(re.split(r"\r\n|\r|\n", block.body))
    return _Body(lines, read_outline(block.body, 1))


def _marked_in(text: str) -> frozenset[str] | None:
    """Find the `##` headings of a text that carry `inherit`.

    Args:
        text: A template's file, or an ancestor's own.

    Returns:
        The key of each such heading, or `None` when the text has no readable
        body.
    """
    body = _read_body(text)
    if body is None:
        return None
    keys = (_marked_key(h) for h in body.headings if h.level == _LEVEL)
    return frozenset(key for key in keys if key is not None)


def _marked_key(heading: Heading) -> str | None:
    """Give the key of a heading whose readable list has `inherit`.

    Args:
        heading: A heading.

    Returns:
        Its key, or `None` for a heading that is indented, has no list, has a list
        that cannot be read or has no `inherit` in it.
    """
    try:
        parsed = read_directive_heading(heading.raw)
    except DirectiveSyntaxError:
        return None
    if parsed is None or not any(isinstance(d, Inherit) for d in parsed.directives):
        return None
    return _key(heading.raw)


def _key(raw: str) -> str | None:
    """Give the key that sections are matched by.

    Args:
        raw: A heading's line.

    Returns:
        Its text without the `#` marks, any directive list, readable or not, a
        closing sequence of `#` marks and the whitespace around it, in lowercase
        for comparison, or `None` for a line that does not start with its marks
        at column 0.
    """
    if _MARKS.match(raw) is None:
        return None
    text = _MARKS.sub("", remove_directive_list(raw), count=1)
    return _CLOSING.sub("", text.strip()).casefold()


def _clean(raw: str) -> str:
    """Take the directive list off a heading line when it can be read.

    Args:
        raw: A heading's line.

    Returns:
        The line without a readable list and right-trimmed, and the line as
        written when it is indented or its list cannot be read.
    """
    if _MARKS.match(raw) is None:
        return raw
    try:
        read_directive_heading(raw)
    except DirectiveSyntaxError:
        return raw
    return remove_directive_list(raw).rstrip()


def _title(heading: Heading) -> str:
    """Give the text of a heading without a readable directive list.

    Args:
        heading: A real heading.

    Returns:
        Its text as `read_outline` found it, less a list that can be read, so
        without a closing sequence of `#` marks.
    """
    try:
        parsed = read_directive_heading(heading.raw)
    except DirectiveSyntaxError:
        return heading.text
    return heading.text if parsed is None else _CLOSING.sub("", parsed.text)


def _section(body: _Body, index: int) -> str:
    """Cut one `##` section out of a body, demoted.

    Args:
        body: The body.
        index: The position of the section's heading among its headings.

    Returns:
        The heading and its text up to the next heading of level 1 or 2, with
        each real heading of it cleaned and demoted, without the blank lines at
        its end, or the empty string when nothing but comments and whitespace
        follows the heading.
    """
    heading = body.headings[index]
    start = heading.line - 1
    end = next(
        (h.line - 1 for h in body.headings[index + 1 :] if h.level <= _LEVEL),
        len(body.lines),
    )
    lines = list(body.lines[start:end])
    if not _COMMENT.sub("", "\n".join(lines[1:])).strip():
        return ""
    for inner in body.headings[index:]:
        if inner.line - 1 >= end:
            break
        lines[inner.line - 1 - start] = _demote(inner)
    return "\n".join(_trim(lines))


def _demote(heading: Heading) -> str:
    """Clean a heading line and put it one level deeper.

    Args:
        heading: A real heading.

    Returns:
        The cleaned line with one more `#`, unchanged in level at 6 and as
        written when it is indented.
    """
    cleaned = _clean(heading.raw)
    if _MARKS.match(cleaned) is None or heading.level >= _DEEPEST:
        return cleaned
    return f"#{cleaned}"


def _trim(lines: list[str]) -> list[str]:
    """Remove the blank lines at both ends.

    Args:
        lines: Lines of text.

    Returns:
        The lines from the first to the last that is not blank.
    """
    kept = [number for number, line in enumerate(lines) if line.strip()]
    return lines[kept[0] : kept[-1] + 1] if kept else []
