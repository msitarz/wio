# SPDX-License-Identifier: Apache-2.0
"""The outline of a Markdown body: the real headings that it holds."""

import re
from typing import TYPE_CHECKING, cast

from wio.formats.markdown import parse
from wio.models.heading import Heading, HeadingLevel

if TYPE_CHECKING:
    from markdown_it.token import Token

_LINE_END = re.compile(r"\r\n|\r|\n")


def read_outline(body: str, start_line: int) -> tuple[Heading, ...]:
    """Find the real headings of a Markdown body.

    A real heading is an ATX heading at the top level of the body, outside code
    and comments: a heading inside a fenced or an indented code block, an HTML
    comment, a blockquote or a list item, and a setext heading, is not one. It
    reads no file, and the Markdown parser is imported on the first call, not
    when `wio.formats` is imported. A line ends at a CRLF, a CR or an LF and at no
    other character, so CRLF and LF read alike and a raw line never ends in a
    carriage return.

    Args:
        body: The body of a file, as the block reader returns it.
        start_line: The line of the file on which the body starts, counted from
            1, so that each heading carries its line in the file.

    Returns:
        The headings in the order they appear, empty for a body without one.
    """
    lines = _LINE_END.split(body)
    tokens = parse(body)
    return tuple(
        _heading(tokens[index + 1], token, lines, start_line)
        for index, token in enumerate(tokens)
        if _is_real_heading(token)
    )


def _is_real_heading(token: Token) -> bool:
    """Tell whether a token opens a real heading.

    Args:
        token: A token of the parsed body.

    Returns:
        Whether it opens an ATX heading at the top level, so not a setext heading
        and not one nested in a quote or a list.
    """
    return (
        token.type == "heading_open"
        and token.level == 0
        and token.markup.startswith("#")
    )


def _heading(
    inline: Token, opening: Token, lines: list[str], start_line: int
) -> Heading:
    """Build the heading that a token opens.

    Args:
        inline: The token after the opening one, which holds the text.
        opening: The token that opens the heading.
        lines: The lines of the body, without their line endings.
        start_line: The line of the file on which the body starts.

    Returns:
        The heading, with its line counted in the file.
    """
    first = (opening.map or [0])[0]
    return Heading(
        level=cast("HeadingLevel", len(opening.markup)),
        text=inline.content,
        raw=lines[first],
        line=start_line + first,
    )
