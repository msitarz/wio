# SPDX-License-Identifier: Apache-2.0
"""The items of a section of a contract, and the judgment of their ids."""

from typing import TYPE_CHECKING

from wio.models.diagnostics import sort_diagnostics
lazy from wio.formats.outline import read_outline

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from wio.models.diagnostics import Diagnostic
    from wio.models.directives import Directive
    from wio.models.heading import Heading
    from wio.models.item import Item, SectionItems


def find_items(
    body: str, start_line: int, heading: Heading, directives: tuple[Directive, ...]
) -> tuple[Item, ...]:
    """Find the items of one section of a Markdown body.

    A section is a `##` heading and runs to the next heading of level 1 or 2. Its
    items are its headings one level below it, and only when it has none, its
    top-level list items that come before its first heading of any deeper level.
    A list item is one item with its nested lists and paragraphs. A comment, a
    code block and a quote hold no items. The id of each item is the match of the
    section's `pattern` directive at the start of its text, and an item has none
    when the section has no pattern. It reads no file, and the Markdown parser is
    imported on the first call, not when `wio.formats` is imported. A line ends at
    a CRLF, a CR or an LF.

    Args:
        body: The text after the metadata block, which holds the section.
        start_line: The file line on which that text begins, from 1, which
            gives each item its own line.
        heading: The section's heading, as `read_outline` returned it for the
            body.
        directives: The directives written on that heading, of which only
            `Pattern` is read.

    Returns:
        The items in the order of the body, empty for a section with none.
    """
    outline = read_outline(body, start_line)
    return _items_of(body, start_line, outline, heading, directives)


def judge_items(path: str, sections: Sequence[SectionItems]) -> tuple[Diagnostic, ...]:
    """Judge the items of the sections of one contract.

    Every finding is an error. Too few items for `items>=N` is at the section's
    heading. An item with no id in a section that has a `pattern` is at the
    item. An id that holds whitespace or a comma is at its item. An id that
    appears more than once in the contract, in one section or in two, is at its
    first occurrence and names the lines of the others, in one error. A section
    with neither `items` nor `pattern` is never a finding.

    Args:
        path: The file of the contract, which each `where` starts with, as
            `path:line`.
        sections: The sections of the contract in the order of the body, each
            with its directives and its items.

    Returns:
        The diagnostics in the order of `sort_diagnostics`: by `where` as a
        string, so line 10 comes before line 2, then by message. Empty when the
        items are sound. A `where` is `path:line`, with the line of the heading
        or the item.
    """
    return sort_diagnostics(_findings(path, sections))


def _items_of(
    body: str,
    start_line: int,
    outline: tuple[Heading, ...],
    heading: Heading,
    directives: tuple[Directive, ...],
) -> tuple[Item, ...]:
    """Find the items of a section and the id of each.

    Args:
        body: The body that holds the section.
        start_line: The file line on which the body begins.
        outline: The real headings of the body, in order.
        heading: The section's heading.
        directives: The directives of the section, of which only `Pattern` is
            read.

    Returns:
        The headings one level below the section, within its extent, and only
        when it has none, its top-level list items that come before its first
        deeper heading, in the order of the body, each with the id that the
        pattern matches at the start of its text, or none.
    """
    raise NotImplementedError


def _findings(path: str, sections: Sequence[SectionItems]) -> Iterator[Diagnostic]:
    """Judge the items of a contract's sections.

    Args:
        path: The file of the contract.
        sections: The sections in the order of the body.

    Returns:
        The findings of the whole contract, in any order: for each section an
        error at its heading when it has fewer items than `items` asks for, at
        each item without an id where it has a pattern, and at each id that holds
        whitespace or a comma, and for each id used more than once one error at
        its first occurrence that names the lines of the others.
    """
    raise NotImplementedError
