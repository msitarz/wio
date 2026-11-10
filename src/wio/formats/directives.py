# SPDX-License-Identifier: Apache-2.0
"""The grammar of the directives on a heading, and the table that documents it."""

import re

from wio.formats.errors import DirectiveSyntaxError
from wio.models.directives import (
    Directive,
    DirectiveHeading,
    DirectiveSpec,
    Inherit,
    Items,
    Pattern,
    Required,
)

DIRECTIVES: tuple[DirectiveSpec, ...] = (
    DirectiveSpec(
        name="required",
        syntax="required",
        meaning="The heading is present in the contract.",
        examples=("## Purpose <!-- wio: required -->",),
    ),
    DirectiveSpec(
        name="items",
        syntax="items>=N",
        meaning="The section holds at least N items, N being 1 or more.",
        examples=("## Goals <!-- wio: items>=1 -->",),
    ),
    DirectiveSpec(
        name="pattern",
        syntax='pattern=<regex> or pattern="<regex>"',
        meaning=(
            "The items of the section match the regular expression, and the "
            "matches are their item ids."
        ),
        examples=(
            "## Acceptance criteria <!-- wio: pattern=AC-\\d+ -->",
            '## Acceptance criteria <!-- wio: pattern="AC-\\d{1,3}" -->',
        ),
    ),
    DirectiveSpec(
        name="inherit",
        syntax="inherit",
        meaning="A descendant's resolved view includes the section.",
        examples=("## Glossary <!-- wio: inherit -->",),
    ),
)
"""Every directive in the order `required`, `items`, `pattern`, `inherit`."""


_HEADING = re.compile(r"(#{1,6})\s+")
_OPENER = re.compile(r"<!--\s*wio:\s*")
_SPACE = re.compile(r"\s*")
_NAME = re.compile(r"[^\s,=<>!]+")
_OPERATOR = re.compile(r"[<>=!~]+")
_TOKEN = re.compile(r"[^\s,]+")
_NAMES = tuple(spec.name for spec in DIRECTIVES)

_UNCLOSED = "A directive list must close on the line of its heading"
_TEXT_AFTER = "A directive list must end its heading"
_SECOND_LIST = "There is one directive list to a heading"
_EMPTY_LIST = "A directive list needs at least one directive"
_NO_NAME = "A directive name is expected here"
_NEEDS_COMMA = "A directive must be followed by a comma or the end of the list"
_ITEMS_SYNTAX = "`items` takes `>=` and a count of 1 or more"
_PATTERN_SYNTAX = "`pattern` takes `=` and a regular expression"
_QUOTE_IN_PLAIN = 'A plain pattern holds no `"`; write it as `\\x22` or quote it'
_UNCLOSED_QUOTE = 'A quoted pattern must close with a `"`'
_AFTER_QUOTE = "Only a comma or the end of the list may follow a quoted pattern"
_EMPTY_PATTERN = "A pattern must not be empty"


def read_directive_heading(line: str) -> DirectiveHeading | None:
    """Read one line as a heading with its directive list.

    A directive list opens with `<!--`, whitespace, the lowercase `wio:` and
    whitespace, ends at the first `-->`, and ends its heading. Any other comment
    is a note and stays in the text. The line is read alone: nothing is read
    from a file.

    Args:
        line: One line of Markdown, without its line ending.

    Returns:
        The heading's text, level and directives in the order written, with no
        directives for a heading without a list, or `None` for a line that is
        not an ATX heading.

    Raises:
        DirectiveSyntaxError: The list names an unknown directive or one in the
            wrong case or twice, is empty, does not close on the line, is
            followed by text or by a second list, or gives a directive a wrong
            value. It carries the column of the first problem.
    """
    heading = _HEADING.match(line)
    if heading is None:
        return None
    level = len(heading[1])
    opener = _OPENER.search(line, heading.end())
    if opener is None:
        return DirectiveHeading(line[heading.end() :].strip(), level, ())
    close = line.find("-->", opener.end())
    if close < 0:
        raise DirectiveSyntaxError(_UNCLOSED, opener.start() + 1)
    _check_tail(line, close + len("-->"))
    text = line[heading.end() : opener.start()].strip()
    directives = _Reader(line[opener.end() : close], opener.end()).directives()
    return DirectiveHeading(text, level, directives)


def _check_tail(line: str, start: int) -> None:
    """Check that nothing but whitespace follows the list.

    Args:
        line: The heading's line.
        start: The index just after the closing `-->`.

    Raises:
        DirectiveSyntaxError: Text or a second list follows the list.
    """
    tail = line[start:]
    text = tail.lstrip()
    if text:
        message = _SECOND_LIST if _OPENER.match(text) else _TEXT_AFTER
        raise DirectiveSyntaxError(message, start + len(tail) - len(text) + 1)


def _unknown(name: str) -> str:
    """Word the error for a name that is not a directive.

    Args:
        name: The name as written.

    Returns:
        A message that lists the directives, and says that names are lowercase
        when only the case is wrong.
    """
    known = ", ".join(f"`{known}`" for known in _NAMES)
    message = f"Unknown directive `{name}`; the directives are {known}"
    if name.lower() in _NAMES:
        message += f"; names are lowercase, so write `{name.lower()}`"
    return message


class _Reader:
    """A cursor over the text between the opener and the closing `-->`.

    Attributes:
        content: The text of the list.
        base: The index of the text in the heading's line, so that a column
            is counted on the line.
        pos: The index of the next character to read in the text.
    """

    content: str
    base: int
    pos: int

    def __init__(self, content: str, base: int) -> None:
        """Start at the beginning of the text.

        Args:
            content: The text of the list.
            base: The index of the text in the heading's line.
        """
        self.content = content
        self.base = base
        self.pos = 0

    def error(self, message: str, at: int | None = None) -> DirectiveSyntaxError:
        """Build an error that names a column of the heading's line.

        Args:
            message: What is wrong.
            at: The index in the text of the offending token, or the cursor.

        Returns:
            The error, whose column is counted from 1.
        """
        index = self.pos if at is None else at
        return DirectiveSyntaxError(message, self.base + index + 1)

    def skip_space(self) -> None:
        """Move the cursor past whitespace."""
        match = _SPACE.match(self.content, self.pos)
        self.pos = match.end() if match else self.pos

    def peek(self) -> str:
        """Give the next character.

        Returns:
            The character at the cursor, or an empty string at the end.
        """
        return self.content[self.pos : self.pos + 1]

    def at_value_end(self) -> bool:
        """Tell whether a directive ends at the cursor.

        Returns:
            Whether the cursor is at a comma or at the end of the list.
        """
        return self.peek() in {"", ","}

    def directives(self) -> tuple[Directive, ...]:
        """Read every directive of the list.

        Returns:
            The directives in the order written.

        Raises:
            DirectiveSyntaxError: The list is empty or has a wrong directive.
        """
        if not self.content.strip():
            raise self.error(_EMPTY_LIST, 0)
        found: list[Directive] = []
        seen: set[str] = set()
        while True:
            found.append(self.directive(seen))
            self.skip_space()
            if self.peek() == "":
                return tuple(found)
            if self.peek() != ",":
                raise self.error(_NEEDS_COMMA)
            self.pos += 1

    def directive(self, seen: set[str]) -> Directive:
        """Read one directive.

        Args:
            seen: The names already read, to which this one is added.

        Returns:
            The directive.

        Raises:
            DirectiveSyntaxError: The name or the value is wrong.
        """
        self.skip_space()
        start = self.pos
        name = self.name(start, seen)
        match name:
            case "items":
                return self.items(start)
            case "pattern":
                return self.pattern(start)
            case "required":
                self.no_value(name)
                return Required()
            case _:
                self.no_value(name)
                return Inherit()

    def name(self, start: int, seen: set[str]) -> str:
        """Read a directive name and check it.

        Args:
            start: The index of the name.
            seen: The names already read, to which this one is added.

        Returns:
            The name of a directive that is known and not yet used.

        Raises:
            DirectiveSyntaxError: There is no name, it is unknown, in the wrong
                case or written twice.
        """
        match = _NAME.match(self.content, start)
        if match is None:
            raise self.error(_NO_NAME)
        name = match[0]
        self.pos = match.end()
        if name not in _NAMES:
            raise self.error(_unknown(name), start)
        if name in seen:
            message = f"The directive `{name}` is written twice"
            raise self.error(message, start)
        seen.add(name)
        return name

    def no_value(self, name: str) -> None:
        """Check that nothing but a comma or the end follows a bare directive.

        Args:
            name: The directive's name.

        Raises:
            DirectiveSyntaxError: Another operator or value follows the name.
        """
        self.skip_space()
        if not self.at_value_end():
            message = f"`{name}` takes no value"
            raise self.error(message)

    def operator(self, start: int, message: str) -> tuple[str, int]:
        """Read the operator after a name.

        Args:
            start: The index of the name, for an error without an operator.
            message: What the directive takes, for an error.

        Returns:
            The operator and its index.

        Raises:
            DirectiveSyntaxError: There is no operator.
        """
        self.skip_space()
        match = _OPERATOR.match(self.content, self.pos)
        if match is None:
            raise self.error(message, start if self.at_value_end() else self.pos)
        self.pos = match.end()
        return match[0], match.start()

    def items(self, start: int) -> Items:
        """Read `items>=N` after its name.

        Args:
            start: The index of the name.

        Returns:
            The directive.

        Raises:
            DirectiveSyntaxError: The operator is not `>=` or the count is not
                a whole number of 1 or more.
        """
        operator, at = self.operator(start, _ITEMS_SYNTAX)
        if operator != ">=":
            raise self.error(_ITEMS_SYNTAX, at)
        self.skip_space()
        token = _TOKEN.match(self.content, self.pos)
        if token is None:
            raise self.error(_ITEMS_SYNTAX, at)
        self.pos = token.end()
        count = token[0]
        if not (count.isascii() and count.isdigit() and int(count) >= 1):
            raise self.error(_ITEMS_SYNTAX, token.start())
        return Items(int(count))

    def pattern(self, start: int) -> Pattern:
        """Read `pattern=<regex>` after its name.

        Args:
            start: The index of the name.

        Returns:
            The directive.

        Raises:
            DirectiveSyntaxError: The operator is not `=`, the pattern is empty
                or malformed, or it does not compile.
        """
        operator, at = self.operator(start, _PATTERN_SYNTAX)
        if operator != "=":
            raise self.error(_PATTERN_SYNTAX, at)
        self.skip_space()
        first = self.pos
        quoted = self.peek() == '"'
        regex = self.quoted(first) if quoted else self.plain(at)
        try:
            re.compile(regex)
        except re.error as error:
            message = f"The pattern does not compile: {error.msg}"
            raise self.error(message, first) from error
        return Pattern(regex)

    def plain(self, operator_at: int) -> str:
        """Read a plain pattern, which runs to the next comma.

        Args:
            operator_at: The index of the `=`, for an empty pattern.

        Returns:
            The pattern trimmed of surrounding spaces.

        Raises:
            DirectiveSyntaxError: The pattern is empty or holds a `"`.
        """
        comma = self.content.find(",", self.pos)
        end = len(self.content) if comma < 0 else comma
        regex = self.content[self.pos : end].rstrip()
        if not regex:
            raise self.error(_EMPTY_PATTERN, operator_at)
        if '"' in regex:
            raise self.error(_QUOTE_IN_PLAIN, self.pos + regex.index('"'))
        self.pos = end
        return regex

    def quoted(self, first: int) -> str:
        """Read a pattern between double quotes, which may hold commas.

        Args:
            first: The index of the opening quote.

        Returns:
            The pattern between the quotes.

        Raises:
            DirectiveSyntaxError: The quote does not close, the pattern is
                empty, or text other than a comma follows the closing quote.
        """
        close = self.content.find('"', first + 1)
        if close < 0:
            raise self.error(_UNCLOSED_QUOTE, first)
        regex = self.content[first + 1 : close]
        if not regex:
            raise self.error(_EMPTY_PATTERN, first)
        self.pos = close + 1
        self.skip_space()
        if not self.at_value_end():
            raise self.error(_AFTER_QUOTE)
        return regex
