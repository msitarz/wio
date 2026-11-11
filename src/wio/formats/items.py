# SPDX-License-Identifier: Apache-2.0
"""The items of a section of a contract, and the judgment of their ids."""

import re
from collections import defaultdict
from typing import TYPE_CHECKING

from wio.models.diagnostics import Diagnostic, sort_diagnostics
from wio.models.directives import Items, Pattern
from wio.models.item import Item
lazy from wio.formats.markdown import parse
lazy from wio.formats.outline import read_outline

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from markdown_it.token import Token

    from wio.models.directives import Directive
    from wio.models.heading import Heading
    from wio.models.item import SectionItems

_SKIPPED = "*_` "
_TOP_LEVEL_ITEM = 1


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
    after = tuple(found for found in outline if found.line > heading.line)
    inside = _until_the_section_ends(after, heading.level)
    below = tuple(found for found in inside if found.level == heading.level + 1)
    plain = tuple(Item(found.text, None, found.line) for found in below) or _list_items(
        body, start_line, heading.line, _line_of_first(after)
    )
    return _with_ids(plain, _pattern(directives))


def _line_of_first(headings: tuple[Heading, ...]) -> int | None:
    """Give the file line of the first of some headings.

    Args:
        headings: Headings in the order of the body.

    Returns:
        The line of the first, or `None` when there is none.
    """
    return headings[0].line if headings else None


def _until_the_section_ends(
    after: tuple[Heading, ...], level: int
) -> tuple[Heading, ...]:
    """Cut the headings after a section's heading where the section ends.

    Args:
        after: The headings that follow the section's heading.
        level: The level of the section's heading.

    Returns:
        The headings before the first one of the same level or above.
    """
    end = next((i for i, found in enumerate(after) if found.level <= level), None)
    return after if end is None else after[:end]


def _list_items(
    body: str, start_line: int, first: int, limit: int | None
) -> tuple[Item, ...]:
    """Find the top-level list items between two lines of a body.

    Args:
        body: The body to parse.
        start_line: The file line on which the body begins.
        first: The file line of the section's heading, which the items follow.
        limit: The file line of the first heading after it, before which the
            items are, or `None` for the end of the body.

    Returns:
        The items with no id, in the order of the body.
    """
    tokens = parse(body)
    return tuple(
        Item(_first_line_of(tokens, index), None, line)
        for index, token in enumerate(tokens)
        if _is_top_level_item(token)
        and first < (line := start_line + (token.map or [0])[0])
        and (limit is None or line < limit)
    )


def _is_top_level_item(token: Token) -> bool:
    """Tell whether a token opens a list item of a list at the top level.

    Args:
        token: A token of the parsed body.

    Returns:
        Whether it opens an item of a list that is neither in a quote nor in
        another item.
    """
    return token.type == "list_item_open" and token.level == _TOP_LEVEL_ITEM


def _first_line_of(tokens: list[Token], index: int) -> str:
    """Read the text of the list item that a token opens.

    Args:
        tokens: The tokens of the body.
        index: The position of the token that opens the item.

    Returns:
        The first line of the item's first paragraph, as written after the
        marker, or the empty text when its first block is not a paragraph.
    """
    if tokens[index + 1].type != "paragraph_open":
        return ""
    return tokens[index + 2].content.split("\n", 1)[0]


def _pattern(directives: tuple[Directive, ...]) -> re.Pattern[str] | None:
    """Compile the pattern directive of a section, if it has one.

    Args:
        directives: The directives of the section.

    Returns:
        The compiled expression, or `None` without a pattern.
    """
    return next(
        (re.compile(d.regex) for d in directives if isinstance(d, Pattern)), None
    )


def _with_ids(
    items: tuple[Item, ...], pattern: re.Pattern[str] | None
) -> tuple[Item, ...]:
    """Give each item the id that the pattern matches at the start of its text.

    Args:
        items: The items of one section, with no id.
        pattern: The section's pattern, or `None`.

    Returns:
        The items in the same order. The id is the match after leading `*`, `_`,
        backticks and spaces, exactly as matched, and none when there is no
        pattern, no match there or an empty match.
    """
    if pattern is None:
        return items
    return tuple(
        Item(item.text, _id_of(item.text, pattern), item.line) for item in items
    )


def _id_of(text: str, pattern: re.Pattern[str]) -> str | None:
    """Find the id at the start of an item's text.

    Args:
        text: The text of the item.
        pattern: The section's pattern.

    Returns:
        The match, or `None` when there is none or it is empty.
    """
    found = pattern.match(text, len(text) - len(text.lstrip(_SKIPPED)))
    return found.group(0) if found and found.group(0) else None


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
    for section in sections:
        yield from _section_findings(path, section)
    yield from _repeat_findings(path, sections)


def _error(path: str, line: int, message: str) -> Diagnostic:
    """Build an error at a line of the contract.

    Args:
        path: The file of the contract.
        line: The line of the finding.
        message: What is wrong.

    Returns:
        The error, whose place is `path:line`.
    """
    return Diagnostic("error", f"{path}:{line}", message)


def _section_findings(path: str, section: SectionItems) -> Iterator[Diagnostic]:
    """Judge one section's items against its own directives.

    Args:
        path: The file of the contract.
        section: The section with its items.

    Returns:
        The errors for too few items, a missing id and an id that is not fit.
    """
    for directive in section.directives:
        match directive:
            case Items(minimum) if len(section.items) < minimum:
                yield _error(
                    path,
                    section.heading.line,
                    f"the `items` directive asks for {_count(minimum)}, and the "
                    f"section holds {_count(len(section.items))}",
                )
            case Pattern(regex):
                yield from _id_findings(path, section.items, regex)


def _id_findings(
    path: str, items: tuple[Item, ...], regex: str
) -> Iterator[Diagnostic]:
    """Judge the ids of the items of a section that has a pattern.

    Args:
        path: The file of the contract.
        items: The items of the section.
        regex: The section's pattern as written.

    Returns:
        An error at each item with no id, and at each id that holds whitespace
        or a comma.
    """
    for item in items:
        if item.id is None:
            yield _error(
                path,
                item.line,
                f"the item has no id matching `{regex}`, which the `pattern` "
                "directive asks for",
            )
        elif re.search(r"[\s,]", item.id):
            yield _error(
                path,
                item.line,
                f"the id `{item.id}` holds whitespace or a comma, which an id cannot",
            )


def _repeat_findings(
    path: str, sections: Sequence[SectionItems]
) -> Iterator[Diagnostic]:
    """Judge the uniqueness of the ids across the sections of a contract.

    Args:
        path: The file of the contract.
        sections: The sections in the order of the body.

    Returns:
        One error for each id used more than once, at its first occurrence,
        naming the lines of the others.
    """
    for id_, (first, *others) in _repeated(sections).items():
        noun = "line" if len(others) == 1 else "lines"
        yield _error(
            path,
            first,
            f"the id `{id_}` is used again on {noun} "
            f"{', '.join(str(line) for line in others)}, and an id is unique in "
            "a contract",
        )


def _repeated(sections: Sequence[SectionItems]) -> dict[str, list[int]]:
    """Collect the lines of each id that is used more than once.

    Args:
        sections: The sections in the order of the body.

    Returns:
        For each id used more than once, in the order of its first occurrence,
        the lines of its items in the order of the body.
    """
    lines: defaultdict[str, list[int]] = defaultdict(list)
    for item in (item for section in sections for item in section.items):
        if item.id is not None:
            lines[item.id].append(item.line)
    return {id_: found for id_, found in lines.items() if len(found) > 1}


def _count(number: int) -> str:
    """Write a number of items.

    Args:
        number: How many items.

    Returns:
        The number and `item` or `items`.
    """
    return f"{number} item" if number == 1 else f"{number} items"
