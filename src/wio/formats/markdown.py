# SPDX-License-Identifier: Apache-2.0
"""The one Markdown parser of `wio.formats`, built on first use."""

from functools import cache
from typing import TYPE_CHECKING

lazy from markdown_it import MarkdownIt

if TYPE_CHECKING:
    from markdown_it.token import Token


@cache
def _parser() -> MarkdownIt:
    """Build the Markdown parser, once.

    Returns:
        A CommonMark parser, which is the definition of a heading, a list and a
        comment block here.
    """
    return MarkdownIt("commonmark")


def parse(body: str) -> list[Token]:
    """Parse a Markdown body into tokens.

    The parser is imported on the first call, not when `wio.formats` is
    imported. It reads a CRLF, a CR and an LF as one line end, so the `map` of a
    token counts the same lines for each.

    Args:
        body: The Markdown to parse.

    Returns:
        The tokens of the body in order, each block with its line range.
    """
    return _parser().parse(body)
