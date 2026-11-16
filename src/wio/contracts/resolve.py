# SPDX-License-Identifier: Apache-2.0
"""The resolved view of a Work: its contract and what its ancestors pass on."""

from typing import TYPE_CHECKING

lazy from wio.models.resolved import InheritedSections, ResolvedContract

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from wio.contracts.ports import TemplateCatalog
    from wio.io.ports import FileSystem
    from wio.models.works import Work


def resolve_work(
    work: Work,
    ancestors: Sequence[Work],
    catalog: TemplateCatalog,
    root: Path,
    files: FileSystem,
) -> ResolvedContract:
    """Resolve a Work against its ancestors.

    It reads the Work's file, each ancestor's file and the file of each template
    an ancestor names, through `files` only, and writes nothing. Everything in
    the result is fixed by those files and the catalog, so the same Work gives
    the same value on every run.

    The Work's own contract is the text after its metadata block, with CRLF read
    as LF, without the blank lines at either end, every comment kept. The
    directive list is taken off every heading of it whose list
    `read_directive_heading` reads, and left as written on a heading whose list
    it rejects.

    An ancestor's source of directives is the template it names, found through
    `catalog`, or its own headings when it names none. Only a level-2 section
    inherits, a section runs to the next heading of level 1 or 2 so a deeper
    heading is content, and every section whose heading matches a marked one,
    by text ignoring case, the whitespace around it and a trailing directive
    list, passes, so a repeated section passes each time. A section that holds
    only comments and whitespace is not passed, and a directive list that cannot
    be read marks nothing. A heading is demoted by one level, never below level
    6, and only when it starts at column 0; an indented heading that
    `read_outline` counts is left as written and never matches a template's.

    An ancestor passes nothing, and the walk goes on to the ancestors above it
    without an error, when the catalog has no template of its name, when
    `is_rejected` rejects it, when the template's file or the ancestor's own file
    cannot be read, a `UnicodeDecodeError` or an `OSError` of `files`. A
    template or an ancestor file that discovery read can fail here, because this
    is its own read.

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
        readable directive list taken off every heading and the blank lines at
        either end removed.
    """
    raise NotImplementedError


def _marked_texts(
    ancestor: Work,
    text: str,
    catalog: TemplateCatalog,
    root: Path,
    files: FileSystem,
) -> frozenset[str] | None:
    """Find the `##` sections that an ancestor's source of directives marks.

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
    raise NotImplementedError


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
    raise NotImplementedError
