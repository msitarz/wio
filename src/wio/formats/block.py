# SPDX-License-Identifier: Apache-2.0
"""The reader of the metadata block that opens a file."""

import re
from typing import TYPE_CHECKING

from wio.formats.errors import MetadataBlockError, TomlSyntaxError
from wio.models.block import MetadataBlock
lazy from wio.formats.toml import decode_toml

if TYPE_CHECKING:
    from wio.models.block import BlockForm

_MARKER_KEY = re.compile(r"^[ \t]*wio[ \t]*=", re.MULTILINE)
_FRONT_MATTER_CLOSE = re.compile(r"^\+\+\+[ \t]*\r?$", re.MULTILINE)
_LINE_END = re.compile(r"\r?\n")
_BYTE_ORDER_MARK = "﻿"
_VERSION = 1
_UNCLOSED_COMMENT = "The metadata block does not close with `-->`"
_UNCLOSED_FRONT_MATTER = "The metadata block does not close with `+++`"
_BAD_MARKER = "The `wio` marker must be the integer 1, the only version wio knows"


def read_metadata_block(text: str) -> MetadataBlock | None:
    """Split a text into its metadata block and its body.

    The block is a `<!-- wio ... -->` comment or `+++` front matter on the
    first line of the text, after an optional leading U+FEFF. The comment ends
    at the first `-->`. CRLF and LF read alike. It reads no file, and it loads
    no TOML decoder for a text that has no block.

    Args:
        text: The text of a file, decoded as UTF-8.

    Returns:
        The block with its form, version, data and body, or `None` for a text
        that has no block, or whose `+++` front matter has no `wio =` in it,
        closed or not.

    Raises:
        MetadataBlockError: The block claims to be wio's but does not close,
            is not valid TOML, or has a `wio` marker other than the integer 1.
            It carries the line of the text.
    """
    first, _, rest = text.removeprefix(_BYTE_ORDER_MARK).partition("\n")
    match first.rstrip():
        case "<!-- wio":
            return _read_comment(rest)
        case "+++":
            return _read_front_matter(rest)
        case _:
            return None


def _read_comment(rest: str) -> MetadataBlock:
    """Read a comment block whose opening line was found.

    Args:
        rest: The text after the opening line, which starts on line 2.

    Returns:
        The block, whose marker is optional.

    Raises:
        MetadataBlockError: The comment does not close, is not valid TOML or
            has a marker other than 1.
    """
    end = rest.find("-->")
    if end < 0:
        raise MetadataBlockError(_UNCLOSED_COMMENT, 1)
    toml_text = rest[:end]
    data, version = _decode_block(toml_text, required=False)
    body, start = _split_body(rest[end + len("-->") :], _line_after(toml_text))
    return _block("comment", version, data, body, start)


def _read_front_matter(rest: str) -> MetadataBlock | None:
    """Read `+++` front matter whose opening line was found.

    Args:
        rest: The text after the opening line, which starts on line 2.

    Returns:
        The block, or `None` when the front matter has no `wio =` in it.

    Raises:
        MetadataBlockError: The front matter is wio's but does not close, is
            not valid TOML or has a marker other than 1.
    """
    close = _FRONT_MATTER_CLOSE.search(rest)
    toml_text = rest if close is None else rest[: close.start()]
    if _MARKER_KEY.search(toml_text) is None:
        return None
    if close is None:
        raise MetadataBlockError(_UNCLOSED_FRONT_MATTER, 1)
    data, version = _decode_block(toml_text, required=True)
    body, start = _split_body(rest[close.end() :], _line_after(toml_text))
    return _block("front-matter", version, data, body, start)


def _line_after(toml_text: str) -> int:
    """Give the line that holds the closing delimiter.

    Args:
        toml_text: The text between the opening line and the delimiter.

    Returns:
        The line of the delimiter, counted from 1, as the text starts on line 2.
    """
    return 2 + toml_text.count("\n")


def _split_body(after: str, line: int) -> tuple[str, int]:
    """Split off the body that follows the closing delimiter.

    Args:
        after: The text after the delimiter.
        line: The line that holds the delimiter.

    Returns:
        The body and its start line: the next line when nothing but the line
        ending follows the delimiter, else the same line.
    """
    ending = _LINE_END.match(after)
    if ending is not None:
        return after[ending.end() :], line + 1
    if not after:
        return "", line + 1
    return after, line


def _decode_block(toml_text: str, *, required: bool) -> tuple[dict[str, object], int]:
    """Decode the TOML of a block and take its marker out.

    Args:
        toml_text: The text between the delimiters, which starts on line 2.
        required: Whether the marker must be present.

    Returns:
        The data without the `wio` key, and the version.

    Raises:
        MetadataBlockError: The TOML is wrong or the marker is not 1, or
            missing when required.
    """
    try:
        data = decode_toml(toml_text)
    except TomlSyntaxError as error:
        raise MetadataBlockError(error.message, error.line + 1) from error
    if "wio" not in data and not required:
        return data, _VERSION
    marker = data.pop("wio", None)
    if type(marker) is not int or marker != _VERSION:
        raise MetadataBlockError(_BAD_MARKER, _marker_line(toml_text))
    return data, marker


def _marker_line(toml_text: str) -> int:
    """Find the line of the `wio` key.

    Args:
        toml_text: The text between the delimiters, which starts on line 2.

    Returns:
        The line of the key in the text, or line 1 when none is found.
    """
    found = _MARKER_KEY.search(toml_text)
    if found is None:
        return 1
    return 2 + toml_text.count("\n", 0, found.start())


def _block(
    form: BlockForm, version: int, data: dict[str, object], body: str, start: int
) -> MetadataBlock:
    """Build the block.

    Args:
        form: The form of the block.
        version: The wio version.
        data: The data without the marker.
        body: The text from the start line on.
        start: The start line of the body.

    Returns:
        The block.
    """
    return MetadataBlock(form, version, data, body, start)
