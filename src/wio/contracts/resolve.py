# SPDX-License-Identifier: Apache-2.0
"""The resolved view of a Work: its contract and what its ancestors pass on."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from wio.contracts.ports import TemplateCatalog
    from wio.io.ports import FileSystem
    from wio.models.resolved import ResolvedContract
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
    raise NotImplementedError


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
    raise NotImplementedError
