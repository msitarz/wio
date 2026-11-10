# SPDX-License-Identifier: Apache-2.0
"""Tests of the directive grammar in `wio.formats`."""

import pytest

from wio.errors import WioError
from wio.formats.directives import DIRECTIVES
from wio.models.directives import (
    Directive,
    DirectiveHeading,
    DirectiveSpec,
    Inherit,
    Items,
    Pattern,
    Required,
)
lazy from wio.formats import DirectiveSyntaxError, read_directive_heading


def _read(line: str) -> DirectiveHeading:
    """Read a line that is a heading.

    Args:
        line: The line.

    Returns:
        The heading with its directives.
    """
    heading = read_directive_heading(line)
    assert heading is not None
    return heading


def test_a_directive_list_is_read_into_typed_directives_in_order() -> None:
    """AC-1: a heading gives its text, level and directives as written."""
    # Given a level-2 heading with `required`, `items>=1` and a pattern
    line = r"## Acceptance criteria <!-- wio: required, items>=1, pattern=AC-\d+ -->"

    # When the parser reads it
    heading = _read(line)

    # Then the text, the level 2 and the directives come in the order written
    assert heading == DirectiveHeading(
        "Acceptance criteria", 2, (Required(), Items(1), Pattern(r"AC-\d+"))
    )


@pytest.mark.parametrize(
    ("line", "text", "directives"),
    [
        ("## Glossary <!-- wio: inherit   -->", "Glossary", (Inherit(),)),
        ("## Goals <!--wio:required ,items>=2 -->", "Goals", (Required(), Items(2))),
        ("## H <!--  wio:  inherit -->", "H", (Inherit(),)),
        (
            r"## C <!-- wio: items >= 2, pattern = AC-\d+ -->",
            "C",
            (Items(2), Pattern(r"AC-\d+")),
        ),
    ],
)
def test_spaces_around_the_parts_of_a_list_are_allowed(
    line: str, text: str, directives: tuple[Directive, ...]
) -> None:
    """AC-1: spaces around `wio:`, the commas, `>=` and `=` change nothing."""
    # Given a heading with spaces, or none, around the parts of its list
    # When the parser reads it
    heading = _read(line)

    # Then it gives the directives that the contract names
    assert (heading.text, heading.directives) == (text, directives)


@pytest.mark.parametrize(
    ("line", "directives"),
    [
        (
            r"## A <!-- wio: pattern=AC-\d+, inherit -->",
            (Pattern(r"AC-\d+"), Inherit()),
        ),
        (
            r'## B <!-- wio: pattern="AC-\d{1,3}", required -->',
            (Pattern(r"AC-\d{1,3}"), Required()),
        ),
        ("## C <!-- wio: pattern=a b -->", (Pattern("a b"),)),
        ('## Q <!-- wio: pattern="a, b" -->', (Pattern("a, b"),)),
    ],
    ids=["plain", "quoted", "inner-space", "quoted-comma"],
)
def test_a_pattern_is_plain_or_between_quotes(
    line: str, directives: tuple[Directive, ...]
) -> None:
    """AC-2: a plain pattern runs to the next comma, a quoted one to its quote."""
    # Given a heading with a plain, a quoted, a spaced or a quoted comma pattern
    # When the parser reads it
    heading = _read(line)

    # Then the pattern is trimmed with inner spaces kept, and a quoted one holds commas
    assert heading.directives == directives


def test_a_literal_quote_and_angle_bracket_are_written_as_hex_escapes() -> None:
    """AC-2: `\\x22` and `\\x3e` stay as written, for `re` to read."""
    # Given a heading whose pattern holds `\x22` and `\x3e`
    line = r"## D <!-- wio: pattern=a\x22b\x3ec -->"

    # When the parser reads it
    heading = _read(line)

    # Then the pattern is kept as written, and `re` reads it as `a"b>c`
    assert heading.directives == (Pattern(r"a\x22b\x3ec"),)


@pytest.mark.parametrize(
    ("line", "text"),
    [
        ("## Purpose", "Purpose"),
        ("## Purpose <!-- a note -->", "Purpose <!-- a note -->"),
        ("## T <!-- wio -->", "T <!-- wio -->"),
        ("## T <!-- WIO: required -->", "T <!-- WIO: required -->"),
        ("## T <!-- wio : required -->", "T <!-- wio : required -->"),
    ],
)
def test_a_line_with_no_directive_list_gives_no_directives_and_no_error(
    line: str, text: str
) -> None:
    """AC-3: notes and near-misses are text, and a non-heading gives `None`."""
    # Given a heading without a list, with a note, or with a near-miss opener
    # When the parser reads it
    heading = _read(line)

    # Then the text keeps its comments and no directives are given
    assert (heading.text, heading.directives) == (text, ())


def test_a_line_that_is_not_a_heading_gives_none() -> None:
    """AC-3: a line without a heading marker is not read."""
    # Given a line of text that carries a list
    line = "Some text <!-- wio: required -->"

    # When the parser reads it
    heading = read_directive_heading(line)

    # Then it gives nothing
    assert heading is None


def test_a_note_before_a_list_stays_in_the_text() -> None:
    """AC-3: a note before the list is part of the heading's text."""
    # Given a heading with a note and then a list
    line = "## Both <!-- a note --> <!-- wio: required -->"

    # When the parser reads it
    heading = _read(line)

    # Then the text keeps the note and the directive is read
    assert heading == DirectiveHeading("Both <!-- a note -->", 2, (Required(),))


@pytest.mark.parametrize(
    ("line", "column", "message"),
    [
        ("## A <!-- wio: mandatory -->", 16, "Unknown directive"),
        ("## B <!-- wio: Required -->", 16, "lowercase"),
        ("## D <!-- wio: required, required -->", 26, "twice"),
        ("## E <!-- wio: -->", 16, "at least one"),
        ("## S <!-- wio: required,", 6, "close on the line of its heading"),
        ("## T <!-- wio: required --> tail", 29, "must end its heading"),
        (
            "## U <!-- wio: required --> <!-- wio: inherit -->",
            29,
            "one directive list to a heading",
        ),
    ],
    ids=["unknown", "case", "twice", "empty", "unclosed", "text-after", "two-lists"],
)
def test_a_list_with_a_wrong_name_or_shape_is_an_error_with_its_column(
    line: str, column: int, message: str
) -> None:
    """AC-4: each wrong list raises an error that names its column."""
    # Given a heading with a wrong name or a wrong shape of list
    # When the parser reads it
    with pytest.raises(DirectiveSyntaxError) as caught:
        read_directive_heading(line)

    # Then the error says what is wrong and names the column, and `str` carries it
    error = caught.value
    assert isinstance(error, WioError)
    assert message in error.message
    assert error.column == column
    assert str(error) == f"{error.message} (column {column})"


@pytest.mark.parametrize(
    ("directive", "column"),
    [
        ("items", 16),
        ("items>=", 21),
        ("items>=0", 23),
        ("items>=-1", 23),
        ("items>=1.5", 23),
        ("items=2", 21),
        ("items>2", 21),
        ("required=1", 24),
        ("required inherit", 25),
        ("pattern=", 23),
        ("pattern=(", 24),
        ('pattern=""', 24),
        ('pattern=a"b', 25),
        ('pattern="a"b', 27),
        ('pattern="AC-', 24),
    ],
)
def test_a_directive_with_a_wrong_value_is_an_error_with_its_column(
    directive: str, column: int
) -> None:
    """AC-5: each wrong value raises an error that names its column."""
    # Given a heading whose directive has a wrong value
    line = f"## I <!-- wio: {directive} -->"

    # When the parser reads it
    with pytest.raises(DirectiveSyntaxError) as caught:
        read_directive_heading(line)

    # Then the error names the column of the offending token
    assert caught.value.column == column
    assert caught.value.message


def test_a_pattern_that_does_not_compile_carries_the_message_of_re() -> None:
    """AC-5: the error of an invalid expression says what `re` says."""
    # Given a heading whose pattern is an unbalanced parenthesis
    line = "## I <!-- wio: pattern=( -->"

    # When the parser reads it
    with pytest.raises(DirectiveSyntaxError) as caught:
        read_directive_heading(line)

    # Then the message holds the message of `re`
    assert "missing ), unterminated subpattern" in caught.value.message


def test_the_level_is_returned_and_not_restricted() -> None:
    """AC-6: a list on a level-3 heading is read and its level is returned."""
    # Given a level-3 heading with a list
    line = "### Notes <!-- wio: required -->"

    # When the parser reads it
    heading = _read(line)

    # Then the level is 3 and the directive is read
    assert heading == DirectiveHeading("Notes", 3, (Required(),))


def test_the_table_lists_every_directive_in_order() -> None:
    """AC-7: the entries are in order, each with a syntax, a meaning, examples."""
    # Given the table of directives
    # When its entries are read in order
    entries = [(spec.name, len(spec.examples)) for spec in DIRECTIVES]

    # Then the names are in order, and `pattern` has two examples and the rest one
    assert entries == [("required", 1), ("items", 1), ("pattern", 2), ("inherit", 1)]
    assert all(spec.syntax and spec.meaning for spec in DIRECTIVES)


@pytest.mark.parametrize("spec", DIRECTIVES, ids=lambda spec: spec.name)
def test_every_example_of_the_table_parses_into_its_directive(
    spec: DirectiveSpec,
) -> None:
    """AC-7: the parser reads each example into the directive it documents."""
    # Given an entry of the table
    kinds = {
        "required": Required,
        "items": Items,
        "pattern": Pattern,
        "inherit": Inherit,
    }

    # When the parser reads each of its examples
    headings = [_read(example) for example in spec.examples]

    # Then each gives the one directive that the entry documents
    assert all(
        len(h.directives) == 1 and isinstance(h.directives[0], kinds[spec.name])
        for h in headings
    )
