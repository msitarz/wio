# SPDX-License-Identifier: Apache-2.0
"""Tests of the items of a section in `wio.formats`."""

from wio.formats import (
    find_items,
    judge_items,
    read_directive_heading,
    read_outline,
)
from wio.models.diagnostics import Diagnostic
from wio.models.item import Item, SectionItems


def _sections(body: str, start_line: int = 1) -> tuple[SectionItems, ...]:
    """Find the items of every `##` section of a body, as a contract is read.

    Args:
        body: The body, whose section headings may carry directives.
        start_line: The file line on which the body starts.

    Returns:
        The sections in the order of the body, with their directives and items.
    """
    sections: list[SectionItems] = []
    for heading in read_outline(body, start_line):
        read = read_directive_heading(heading.raw)
        if heading.level == 2 and read is not None:
            items = find_items(body, start_line, heading, read.directives)
            sections.append(SectionItems(heading, read.directives, items))
    return tuple(sections)


def _first_items(body: str, start_line: int = 1) -> tuple[Item, ...]:
    """Find the items of the first section of a body.

    Args:
        body: The body.
        start_line: The file line on which the body starts.

    Returns:
        The items of its first `##` section.
    """
    return _sections(body, start_line)[0].items


def _joined(*blocks: str) -> str:
    """Join blocks of Markdown with a blank line between them.

    Args:
        *blocks: The blocks.

    Returns:
        The blocks as one body.
    """
    return "\n\n".join(blocks) + "\n"


def test_the_subheadings_of_a_section_are_its_items_and_win_over_a_list() -> None:
    """AC-1: the headings one level below the section, with their text and file line."""
    # Given a body starting at line 10 with an intro bullet, two `###` criteria
    # around a `####` heading, and a next section with a `###` heading
    body = _joined(
        "## Acceptance criteria",
        "- intro",
        "### **AC-1** First",
        "#### Scenario",
        "### **AC-2** Second",
        "## Next",
        "### X",
    )

    # When the items of the section are found
    found = _first_items(body, 10)

    # Then the two criteria are returned in order on lines 14 and 18, and
    # the bullet, the `####` heading and the next section's heading are not items
    assert found == (
        Item("**AC-1** First", None, 14),
        Item("**AC-2** Second", None, 18),
    )


def test_the_list_items_of_a_section_are_its_items_when_it_has_no_subheading() -> None:
    """AC-1: top-level list items, ordered or not, in a body with CRLF endings."""
    # Given a CRLF body with a bullet that has a nested one, a numbered item, a
    # quoted list, a comment with a list and a fenced block with a list
    body = _joined(
        "## Goals",
        "- one\n  - sub",
        "1. two",
        "> - quoted",
        "<!--\n- hidden\n-->",
        "```\n- code\n```",
    ).replace("\n", "\r\n")

    # When the items of the section are found
    found = _first_items(body)

    # Then they are `one` on line 3 and `two` on line 6, and nothing else
    assert found == (Item("one", None, 3), Item("two", None, 6))


def test_a_list_after_a_deeper_heading_is_not_an_item() -> None:
    """AC-1: only the list items before the first deeper heading count."""
    # Given a section with a bullet, a `####` heading and a bullet under it
    body = _joined("## Notes", "- before", "#### Part", "- after")

    # When its items are found
    found = _first_items(body)

    # Then the only item is the first bullet
    assert found == (Item("before", None, 3),)


def test_a_list_item_that_opens_with_a_code_block_has_empty_text_and_no_id() -> None:
    """AC-1: no paragraph first gives the empty text and one error."""
    # Given a section with pattern `N-\d+` and a list item that opens with a
    # fenced block
    body = _joined("## Notes <!-- wio: pattern=N-\\d+ -->", "-\n  ```\n  - code\n  ```")

    # When its items are found and judged
    sections = _sections(body)
    judged = judge_items("c.md", sections)

    # Then the item has the empty text and no id, and there is one error
    assert sections[0].items == (Item("", None, 3),)
    assert [d.where for d in judged] == ["c.md:3"]


def test_a_section_with_only_prose_or_a_comment_has_no_items() -> None:
    """AC-1: prose and an authoring comment hold no item."""
    # Given a section of prose and a section of one authoring comment
    body = _joined("## Prose", "Only words.", "## Comment", "<!-- - hidden -->")

    # When the items of each are found
    found = [section.items for section in _sections(body)]

    # Then both have none
    assert found == [(), ()]


def test_the_id_is_the_pattern_match_after_leading_markup() -> None:
    """AC-2: the match at the start, after `*`, `_`, backticks and spaces."""
    # Given pattern `AC-\d+` and items with markup, a mid-text id and a prefix
    body = _joined(
        "## Criteria <!-- wio: pattern=AC-\\d+ -->",
        "### **AC-1** First",
        "### `AC-2` Second",
        "### Replaces AC-3",
        "### AC-12 twelve",
        "### First AC-4",
    )

    # When the items are found
    found = _first_items(body)

    # Then the ids are `AC-1`, `AC-2`, none, `AC-12` and none
    assert [item.id for item in found] == ["AC-1", "AC-2", None, "AC-12", None]


def test_a_list_item_has_its_id_after_its_marker() -> None:
    """AC-2: bullets and numbered items give their ids."""
    # Given pattern `A-\d+` and the list items `- **A-1**: first` and `2. A-2 second`
    body = _joined(
        "## Assumptions <!-- wio: pattern=A-\\d+ -->",
        "- **A-1**: first\n\n2. A-2 second",
    )

    # When the items are found
    found = _first_items(body)

    # Then the ids are `A-1` and `A-2`
    assert [item.id for item in found] == ["A-1", "A-2"]


def test_an_empty_match_is_no_id() -> None:
    """AC-2: the pattern `\\d*` gives no id for `Plain` and `7` for `7 seven`."""
    # Given pattern `\d*` and the items `Plain` and `7 seven`
    body = _joined("## Items <!-- wio: pattern=\\d* -->", "### Plain", "### 7 seven")

    # When the items are found
    found = _first_items(body)

    # Then the first has no id and the second has the id `7`
    assert [item.id for item in found] == [None, "7"]


def test_a_section_without_a_pattern_gives_no_ids() -> None:
    """AC-2: no pattern, no id."""
    # Given a section with items and no pattern
    body = _joined("## Goals", "- AC-1 one", "- AC-2 two")

    # When the items are found
    found = _first_items(body)

    # Then none has an id
    assert [item.id for item in found] == [None, None]


def test_too_few_items_is_an_error_at_the_heading() -> None:
    """AC-3: `items>=3` on two items, and `items>=1` on a comment only."""
    # Given `items>=3` on a section with two items and `items>=1` on a section
    # of a comment
    body = _joined(
        "## Goals <!-- wio: items>=3 -->",
        "- one\n- two",
        "## Notes <!-- wio: items>=1 -->",
        "<!-- authoring comment -->",
    )

    # When the items are judged
    judged = judge_items("c.md", _sections(body))

    # Then each is an error at its heading that names `items` and says how many
    # items it holds and needs
    assert judged == (
        Diagnostic(
            "error",
            "c.md:1",
            "the `items` directive asks for 3 items, and the section holds 2 items",
        ),
        Diagnostic(
            "error",
            "c.md:6",
            "the `items` directive asks for 1 item, and the section holds 0 items",
        ),
    )


def test_an_item_without_an_id_is_an_error_at_the_item() -> None:
    """AC-3: one error at the item `Replaces AC-3`, none for the others."""
    # Given pattern `AC-\d+` on a section whose second item is `Replaces AC-3`
    body = _joined(
        "## Criteria <!-- wio: pattern=AC-\\d+ -->",
        "### AC-1 one",
        "### Replaces AC-3",
        "### AC-2 two",
    )

    # When the items are judged
    judged = judge_items("c.md", _sections(body))

    # Then one error at that line names `pattern`, and none is for the others
    assert judged == (
        Diagnostic(
            "error",
            "c.md:5",
            "the item has no id matching `AC-\\d+`, which the `pattern` directive "
            "asks for",
        ),
    )


def test_unmarked_items_are_free() -> None:
    """AC-3: neither `items` nor `pattern` gives no diagnostic."""
    # Given a section with items and no directive
    body = _joined("## Goals", "- one\n- two")

    # When the items are judged
    judged = judge_items("c.md", _sections(body))

    # Then there is no diagnostic
    assert judged == ()


def test_a_repeated_id_is_one_error_at_the_first_occurrence() -> None:
    """AC-4: in one section or two, naming the lines of the others."""
    # Given `AC-1` twice in one section and once in the next, on lines 12, 14 and 18
    body = _joined(
        "## Criteria <!-- wio: pattern=AC-\\d+ -->",
        "- **AC-1** a",
        "- **AC-1** b",
        "## Other <!-- wio: pattern=AC-\\d+ -->",
        "- **AC-1** c",
    )

    # When the items are judged
    judged = judge_items("c.md", _sections(body, 10))

    # Then one error at line 12 names `AC-1` and the lines 14 and 18
    assert judged == (
        Diagnostic(
            "error",
            "c.md:12",
            "the id `AC-1` is used again on lines 14, 18, and an id is unique in a "
            "contract",
        ),
    )


def test_an_id_with_whitespace_or_a_comma_is_an_error_at_its_item() -> None:
    """AC-4: patterns `AC \\d` and `A,\\d` give bad ids."""
    # Given the two patterns and the items `AC 1` and `A,1`
    body = _joined(
        '## Spaced <!-- wio: pattern="AC \\d" -->',
        "- AC 1",
        '## Comma <!-- wio: pattern="A,\\d" -->',
        "- A,1",
    )

    # When the items are judged
    judged = judge_items("c.md", _sections(body))

    # Then each is an error at its line that says the id holds whitespace or a comma
    assert [(d.where, "whitespace or a comma" in d.message) for d in judged] == [
        ("c.md:3", True),
        ("c.md:7", True),
    ]
