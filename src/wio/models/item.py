# SPDX-License-Identifier: Apache-2.0
"""The types of an item of a section and of a section whose items are judged."""

from dataclasses import dataclass

lazy from wio.models.directives import Directive
lazy from wio.models.heading import Heading


@dataclass(frozen=True)
class Item:
    """An item of a section: a subheading, or else a top-level list item.

    It is immutable. Provisional: the implementation stage may rename its
    fields.

    Attributes:
        text: The Markdown of the item as written: a heading's text as
            `read_outline` gives it, or the first line of a list item after its
            marker. A list item whose first block is not a paragraph has an
            empty text.
        id: The match of the section's `pattern` at the start of the text, after
            leading `*`, `_`, backticks and spaces, exactly as matched. `None`
            when the section has no pattern, the pattern does not match there,
            or the match is empty.
        line: The line of the item in the file, counted from 1.
    """

    text: str
    id: str | None
    line: int


@dataclass(frozen=True)
class SectionItems:
    """A section of a contract with its directives and the items found in it.

    It is immutable, and is what the judge of items takes. Provisional: the
    implementation stage may rename its fields.

    Attributes:
        heading: The section's `##` heading.
        directives: The directives written on that heading.
        items: The items of the section in the order of the body.
    """

    heading: Heading
    directives: tuple[Directive, ...]
    items: tuple[Item, ...]
