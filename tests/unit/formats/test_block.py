# SPDX-License-Identifier: Apache-2.0
"""Tests of the reader of the metadata block in `wio.formats`."""

import pytest

from wio.errors import WioError
lazy from wio.formats import MetadataBlockError, read_metadata_block

COMMENT = '<!-- wio\nid = "k3m9xq"\n-->\n\n# Title'
FRONT_MATTER = '+++\nwio = 1\nid = "k3m9xq"\n+++\n\n# Title'


def _read(text: str) -> tuple[str, int, dict[str, object], int]:
    """Read a text that has a block.

    Args:
        text: The text.

    Returns:
        The form, version, data and body start line of its block.
    """
    block = read_metadata_block(text)
    assert block is not None
    return block.form, block.version, block.data, block.body_start_line


def test_the_comment_form_gives_its_parts_and_its_body() -> None:
    """AC-1: a comment block gives form, version, data and the body after it."""
    # Given a comment block followed by an empty line and a title
    text = COMMENT

    # When it is read
    block = read_metadata_block(text)

    # Then the parts are those of the contract and the body starts on line 4
    assert block is not None
    assert (block.form, block.version, block.data) == ("comment", 1, {"id": "k3m9xq"})
    assert (block.body, block.body_start_line) == ("\n# Title", 4)


def test_text_after_the_closing_delimiter_starts_the_body() -> None:
    """AC-1: the body begins on the line of `-->` when text follows it."""
    # Given a comment block whose closing line carries a title
    text = '<!-- wio\nid = "k3m9xq"\n--> # Title'

    # When it is read
    block = read_metadata_block(text)

    # Then the body is a space and the title, starting on line 3
    assert block is not None
    assert (block.body, block.body_start_line) == (" # Title", 3)


def test_the_body_is_kept_byte_for_byte() -> None:
    """AC-1: CRLF endings stay in the body, and a block alone leaves it empty."""
    # Given a CRLF block with a title, and the same block with nothing after
    crlf = '<!-- wio\r\nid = "k3m9xq"\r\n-->\r\n# Title\r\n'
    bare = '<!-- wio\r\nid = "k3m9xq"\r\n-->\r\n'

    # When each is read
    with_title = read_metadata_block(crlf)
    without = read_metadata_block(bare)

    # Then the first body is the title with its CRLF and the second is empty
    assert with_title is not None
    assert (with_title.body, with_title.body_start_line) == ("# Title\r\n", 4)
    assert without is not None
    assert without.body == ""


def test_the_front_matter_form_gives_its_parts_without_the_marker() -> None:
    """AC-1: `+++` front matter gives its form, and its data lacks `wio`."""
    # Given `+++` front matter followed by an empty line and a title
    text = FRONT_MATTER

    # When it is read
    form, version, data, start = _read(text)

    # Then the form is front matter, the data has no marker and the body is on 5
    assert (form, version, data, start) == ("front-matter", 1, {"id": "k3m9xq"}, 5)


def test_an_absent_marker_in_a_comment_is_version_1() -> None:
    """AC-2: a comment block with no marker and one with `wio = 1` agree."""
    # Given comment blocks without a marker and with `wio = 1`
    bare = '<!-- wio\nid = "k3m9xq"\n-->'
    marked = '<!-- wio\nwio = 1\nid = "k3m9xq"\n-->'

    # When each is read
    results = [_read(bare)[1:3], _read(marked)[1:3]]

    # Then both give version 1 and data without a `wio` key
    assert results == [(1, {"id": "k3m9xq"})] * 2


@pytest.mark.parametrize("marker", ["2", "true", '"1"', "1.0"])
@pytest.mark.parametrize("form", ["comment", "front-matter"])
def test_a_marker_that_is_not_the_integer_1_is_refused(form: str, marker: str) -> None:
    """AC-2: only the integer 1 is a marker, in either form."""
    # Given a block of the form whose marker is the value
    text = (
        f"<!-- wio\nwio = {marker}\n-->"
        if form == "comment"
        else f"+++\nwio = {marker}\n+++"
    )

    # When it is read
    with pytest.raises(MetadataBlockError) as caught:
        read_metadata_block(text)

    # Then the error says the marker must be the integer 1, at its line
    assert isinstance(caught.value, WioError)
    assert "must be the integer 1" in caught.value.message
    assert caught.value.line == 2


@pytest.mark.parametrize(
    "text",
    [
        "# Title\n",
        "\n<!-- wio\nid = 1\n-->",
        '# Title\n<!-- wio\nid = "k"\n-->',
        '<!-- wiox\nid = "k"\n-->',
        '+++\nid = "k"\n+++\n',
        '+++\nid = "k"\n',
    ],
    ids=[
        "no-block",
        "blank-first-line",
        "late-comment",
        "other-marker",
        "front-matter-not-wios",
        "unclosed-front-matter-not-wios",
    ],
)
def test_a_text_that_is_not_marked_gives_nothing(text: str) -> None:
    """AC-3: a text without wio's block gives `None` and raises nothing."""
    # Given a text that is not marked
    # When it is read
    block = read_metadata_block(text)

    # Then it gives nothing
    assert block is None


@pytest.mark.parametrize(
    ("text", "line", "message"),
    [
        ('<!-- wio\nid = "k"', 1, "does not close"),
        ('<!-- wio\nid = "k"\nid =\n-->', 3, ""),
        ('<!-- wio\ns = "a-->b"\n-->', 2, "Unterminated string"),
        ('+++\nwio = 1\nid = "k"\n', 1, "does not close"),
        ("+++\nwio = 1\nid =\n+++", 3, ""),
    ],
    ids=[
        "unclosed-comment",
        "invalid-toml-comment",
        "first-closing-delimiter",
        "unclosed-front-matter",
        "invalid-toml-front-matter",
    ],
)
def test_a_block_that_cannot_be_read_is_an_error_with_its_line(
    text: str, line: int, message: str
) -> None:
    """AC-4: an unclosed or invalid block raises an error at its line."""
    # Given a block that cannot be read
    # When it is read
    with pytest.raises(MetadataBlockError) as caught:
        read_metadata_block(text)

    # Then the error names the line of the text, and `str` carries it
    assert caught.value.line == line
    assert message in caught.value.message
    assert str(caught.value) == f"{caught.value.message} (line {line})"


@pytest.mark.parametrize("text", [COMMENT, FRONT_MATTER])
def test_line_endings_and_the_byte_order_mark_do_not_change_the_result(
    text: str,
) -> None:
    """AC-5: LF, CRLF and a leading U+FEFF read alike."""
    # Given one block written with LF, with CRLF and with a leading U+FEFF
    variants = [text, text.replace("\n", "\r\n"), "\ufeff" + text]

    # When each is read
    results = [_read(variant) for variant in variants]

    # Then the form, the version, the data and the body start line are equal,
    # and the body is the same text with the endings it had
    assert results[0] == results[1] == results[2]
    bodies = [read_metadata_block(variant) for variant in variants]
    assert [b.body if b else None for b in bodies] == [
        "\n# Title",
        "\r\n# Title",
        "\n# Title",
    ]
