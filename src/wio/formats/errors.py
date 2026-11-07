# SPDX-License-Identifier: Apache-2.0
"""The errors of `wio.formats`."""

from wio.errors import WioError


class TomlSyntaxError(WioError):
    """A text that is not valid TOML, with where its first problem is.

    It names no file: the caller knows which file it decoded and adds that.
    `str` of it is `<message> (line <line>, column <column>)`.

    Attributes:
        message: What `tomllib` found wrong, without the position.
        line: The line of the first problem, counted from 1.
        column: The column of the first problem, counted from 1.
    """

    message: str
    line: int
    column: int

    def __init__(self, message: str, line: int, column: int) -> None:
        """Keep the message and the position, and build the text of `str`.

        Args:
            message: What is wrong, without the position.
            line: The line of the first problem, counted from 1.
            column: The column of the first problem, counted from 1.
        """
        super().__init__(f"{message} (line {line}, column {column})")
        self.message = message
        self.line = line
        self.column = column
