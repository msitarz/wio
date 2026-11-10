# SPDX-License-Identifier: Apache-2.0
"""The outline of a Markdown body: the real headings that it holds."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.models.heading import Heading


def read_outline(body: str, start_line: int) -> tuple[Heading, ...]:
    """Find the real headings of a Markdown body.

    A real heading is an ATX heading at the top level of the body, outside code
    and comments: a heading inside a fenced or an indented code block, an HTML
    comment, a blockquote or a list item, and a setext heading, is not one. It
    reads no file, and the Markdown parser is imported on the first call, not
    when `wio.formats` is imported. CRLF and LF read alike.

    Args:
        body: The body of a file, as the block reader returns it.
        start_line: The line of the file on which the body starts, counted from
            1, so that each heading carries its line in the file.

    Returns:
        The headings in the order they appear, empty for a body without one.
    """
    raise NotImplementedError
