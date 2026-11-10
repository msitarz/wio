# SPDX-License-Identifier: Apache-2.0
"""The type of a heading found in the body of a Markdown file."""

from dataclasses import dataclass
from typing import Literal

type HeadingLevel = Literal[1, 2, 3, 4, 5, 6]


@dataclass(frozen=True)
class Heading:
    """A real heading of a Markdown body: an ATX heading at the top level.

    It is immutable. It is not a `DirectiveHeading`, which reads the directive
    list of one line.

    Attributes:
        level: The number of `#` marks, 1 to 6.
        text: What the heading says, without the leading `#` marks, a closing
            sequence of `#` marks or the spaces around it.
        raw: The whole line as written, without its line ending. For a heading on
            the first line of a body that began in the middle of a line, it is
            that line as the body holds it, without what came before.
        line: The line of the heading in the file, counted from 1.
    """

    level: HeadingLevel
    text: str
    raw: str
    line: int
