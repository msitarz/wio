# SPDX-License-Identifier: Apache-2.0
"""Tests of the outline of a Markdown body in `wio.formats`."""

import pytest

from wio.models.heading import Heading
lazy from wio.formats import read_outline

LOOKALIKES = {
    "backtick-fence": "```\n# Inside\n```\n\n## Real",
    "tilde-fence": "~~~\n# Inside\n~~~\n\n## Real",
    "comment": "<!--\n# Inside\nmore\n-->\n\n## Real",
    "indented-code": "    # Inside\n\n## Real",
    "blockquote": "> ## Quoted\n\n## Real",
    "list-item": "- ## Listed\n\n## Real",
    "setext": "A paragraph\n====\n\n## Real",
}


def test_the_headings_come_with_their_level_text_raw_line_and_file_line() -> None:
    """AC-1: each real heading is returned in order, with its four fields."""
    # Given a body with headings of level 1, 2 and 6, starting on line 10
    body = "# A\n\n## B <!-- wio: required -->\n\n###### F"

    # When the outline reads it
    found = read_outline(body, 10)

    # Then three headings are returned, with their level, text, raw line and line
    assert found == (
        Heading(1, "A", "# A", 10),
        Heading(2, "B <!-- wio: required -->", "## B <!-- wio: required -->", 12),
        Heading(6, "F", "###### F", 14),
    )


def test_a_body_that_starts_in_the_middle_of_a_line_keeps_that_line_as_it_is() -> None:
    """AC-1: a heading on the body's first line has its start line and its raw text."""
    # Given a body that is ` # Title` followed by a paragraph, starting on line 3
    body = " # Title\nText"

    # When the outline reads it
    found = read_outline(body, 3)

    # Then the heading has the text `Title`, the raw line ` # Title` and line 3
    assert found == (Heading(1, "Title", " # Title", 3),)


def test_a_body_without_a_heading_has_no_headings() -> None:
    """AC-1: two paragraphs give nothing."""
    # Given a body of two paragraphs
    body = "First paragraph.\n\nSecond paragraph.\n"

    # When the outline reads it
    found = read_outline(body, 1)

    # Then it returns no headings
    assert found == ()


def test_the_text_leaves_out_the_marks_and_spaces_around_it() -> None:
    """AC-2: no leading or closing `#` marks, no spaces, and the raw line is whole."""
    # Given a closed heading, and a spaced one that is followed by two spaces
    body = "## Title ##\n##   Spaced  ##  \n"

    # When the outline reads them
    found = read_outline(body, 1)

    # Then the texts are bare and each raw line is the whole line, spaces kept
    assert [(h.text, h.raw) for h in found] == [
        ("Title", "## Title ##"),
        ("Spaced", "##   Spaced  ##  "),
    ]


@pytest.mark.parametrize("body", LOOKALIKES.values(), ids=LOOKALIKES.keys())
def test_a_line_that_only_looks_like_a_heading_is_not_one(body: str) -> None:
    """AC-3: code, comments, quotes, lists and setext lines hold no heading."""
    # Given a body with a look-alike and then a real heading
    real_line = body.splitlines().index("## Real") + 1

    # When the outline reads it, from line 1
    found = read_outline(body, 1)

    # Then it returns the real heading only, on the line it is on in the body
    assert found == (Heading(2, "Real", "## Real", real_line),)


def test_line_endings_do_not_change_the_headings() -> None:
    """AC-4: CRLF and LF give equal results, and no raw line ends in a CR."""
    # Given one body written with LF and with CRLF
    lf = "# A\n\ntext\n\n## B\n"
    crlf = lf.replace("\n", "\r\n")

    # When the outline reads both
    from_lf = read_outline(lf, 1)
    from_crlf = read_outline(crlf, 1)

    # Then the results are equal and no raw line ends in a carriage return
    assert from_lf == from_crlf
    assert not any(h.raw.endswith("\r") for h in from_crlf)


def test_a_form_feed_and_a_next_line_character_are_no_line_ending() -> None:
    """AC-4: only CRLF, CR and LF end a line, so the lines of a heading hold."""
    # Given a paragraph with a form feed and a next-line character before a heading
    body = "text\x0c\x85 more\n\n## Real\n"

    # When the outline reads it
    found = read_outline(body, 1)

    # Then the heading is on line 3
    assert found == (Heading(2, "Real", "## Real", 3),)
