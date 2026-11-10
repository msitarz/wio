# SPDX-License-Identifier: Apache-2.0
"""The errors of `wio.formats`."""

from typing import ClassVar, override

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


class _PlacedError(WioError):
    """A `WioError` whose text is the message and where it happened.

    A subclass names the unit of the position in `unit` and declares the
    attribute of that name, which holds the position.

    Attributes:
        message: What is wrong, without the position.
    """

    unit: ClassVar[str]
    message: str

    def __init__(self, message: str, position: int) -> None:
        """Keep the message and the position, and build the text of `str`.

        Args:
            message: What is wrong, without the position.
            position: Where the problem is, counted from 1, in the unit of the
                subclass.
        """
        super().__init__(f"{message} ({self._where(position)})")
        self.message = message
        setattr(self, self.unit, position)

    def _where(self, position: int) -> str:
        """Word where the problem is, for the text of `str`.

        Args:
            position: The position in the unit of the subclass.

        Returns:
            The unit and the position, such as `line 3`.
        """
        return f"{self.unit} {position}"


class MetadataBlockError(_PlacedError):
    """A metadata block that claims to be wio's but cannot be read.

    It names no file: the caller knows which file it read and adds that.
    `str` of it is `<message> (line <line>)`.

    Attributes:
        message: What is wrong with the block, without the position.
        line: The line of the text that the reader was given, counted from 1,
            where the problem is.
    """

    unit = "line"
    line: int


class DirectiveSyntaxError(_PlacedError):
    """A directive list that is wrong, with the column of its first problem.

    It names no file and no line: the caller knows which line it read.
    `str` of it is `<message> (column <column>)`.

    Attributes:
        message: What is wrong, without the position.
        column: The column of the first character of the offending token,
            counted from 1 on the heading's line.
    """

    unit = "column"
    column: int


class NotATemplateError(WioError):
    """A text that has no wio metadata block, so it is not a template.

    It names no file: the caller knows which file it read and adds that.
    """


class TemplateDirectiveError(DirectiveSyntaxError):
    """A directive list that is wrong, with the line of its heading in the text.

    It is the error that preparing a skeleton raises for a wrong directive list.
    It names no file: the caller knows which file it read. `str` of it is
    `<message> (line <line>, column <column>)`.

    Attributes:
        line: The line of the heading in the text that the reader was given,
            counted from 1.
    """

    line: int

    def __init__(self, message: str, column: int, line: int) -> None:
        """Keep the line, and the message and the column as the parent does.

        Args:
            message: What is wrong, without the position.
            column: The column of the problem on the heading's line, counted
                from 1.
            line: The line of the heading in the text, counted from 1.
        """
        self.line = line
        super().__init__(message, column)

    @override
    def _where(self, position: int) -> str:
        """Word where the problem is: the line of the heading and the column.

        Args:
            position: The column.

        Returns:
            The line and the column, such as `line 7, column 5`.
        """
        return f"line {self.line}, column {position}"
