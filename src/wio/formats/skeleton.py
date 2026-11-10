# SPDX-License-Identifier: Apache-2.0
"""Preparing a template as the skeleton of a contract."""

import re
from collections.abc import Mapping
from typing import TYPE_CHECKING

from wio.formats.block import read_metadata_block
from wio.formats.directives import read_directive_heading, remove_directive_list
from wio.formats.errors import (
    DirectiveSyntaxError,
    NotATemplateError,
    TemplateDirectiveError,
)
from wio.formats.outline import read_outline
from wio.formats.writer import encode_toml

if TYPE_CHECKING:
    from wio.models.block import BlockForm, MetadataBlock
    from wio.models.heading import Heading

_BYTE_ORDER_MARK = "﻿"
_LINE_ENDING = re.compile(r"\r\n|\r|\n")
_KEEPING_ENDINGS = re.compile(r"(\r\n|\r|\n)")
_NOT_A_TEMPLATE = "The text has no wio metadata block, so it is not a template"
_DROPPED = frozenset({"id", "template"})


def prepare_skeleton(name: str, text: str) -> str:
    """Prepare a template as the skeleton of a contract that follows it.

    The skeleton is the text of a contract without its `id`: a metadata block of
    the template's own form, holding `template` and then the keys and the tables
    of the template's `[contract]` table in the order the template wrote them,
    and the template's body with the directive list taken off each real heading.
    The template's own keys, such as `kind`, `shape`, `description` and
    `[actions]`, the metadata's comments, and an `id` or a `template` inside
    `[contract]` are dropped. A comment block never gets the marker, and `+++`
    front matter has `wio = 1` as its first key. The block is written with the
    line ending of the template's first line and ends with it, and the body
    follows as it was. A leading byte-order mark is kept at the start of the
    skeleton, and the line ending is that of the first line after it. The raw
    line of a heading never ends in a carriage return, so the list and the spaces
    before it are removed from the raw line and the line ending of a CRLF
    template stays. The same template always gives the same skeleton. It reads
    no file, and `tomlkit` is imported on the first call, not when `wio.formats`
    is imported.

    Args:
        name: The template's name, which is its file's name without `.md`.
        text: The template's text, as the block reader reads it.

    Returns:
        The skeleton's text.

    Raises:
        NotATemplateError: The text has no wio metadata block.
        MetadataBlockError: The block cannot be read, as the block reader says.
        TemplateDirectiveError: A real heading's directive list is wrong. It
            carries the line of the heading in the text and the column of the
            problem.
    """
    block = read_metadata_block(text)
    if block is None:
        raise NotATemplateError(_NOT_A_TEMPLATE)
    mark = _BYTE_ORDER_MARK if text.startswith(_BYTE_ORDER_MARK) else ""
    ending = _first_line_ending(text.removeprefix(_BYTE_ORDER_MARK))
    head = _write_block(block.form, _metadata(name, block.data), ending)
    return mark + head + _strip_lists(block)


def _first_line_ending(text: str) -> str:
    """Find the line ending that a skeleton's block is written with.

    Args:
        text: The template's text without a byte-order mark.

    Returns:
        A CRLF when the first line ends with one, otherwise an LF.
    """
    found = _LINE_ENDING.search(text)
    return "\r\n" if found is not None and found[0] == "\r\n" else "\n"


def _metadata(name: str, data: Mapping[str, object]) -> dict[str, object]:
    """Pick what a contract's metadata holds out of a template's metadata.

    Args:
        name: The template's name.
        data: The template's metadata, without the marker.

    Returns:
        `template`, then the keys and tables of `[contract]` in the order they
        were written, without an `id` or a `template` of their own.
    """
    contract = data.get("contract")
    kept = (
        {key: value for key, value in contract.items() if key not in _DROPPED}
        if isinstance(contract, Mapping)
        else {}
    )
    return {"template": name, **kept}


def _write_block(form: BlockForm, data: Mapping[str, object], ending: str) -> str:
    """Write a metadata block of the given form.

    Args:
        form: `"comment"` or `"front-matter"`.
        data: The metadata to write.
        ending: The line ending to write the block with.

    Returns:
        The block, ending in a line ending; front matter starts with the marker.
    """
    toml = encode_toml(data).replace("\n", ending)
    if form == "comment":
        return f"<!-- wio{ending}{toml}-->{ending}"
    return f"+++{ending}wio = 1{ending}{toml}+++{ending}"


def _strip_lists(block: MetadataBlock) -> str:
    """Take the directive list off each real heading of a template's body.

    Args:
        block: The template's block with its body and the body's start line.

    Returns:
        The body, otherwise as it was.

    Raises:
        TemplateDirectiveError: A real heading's list is wrong.
    """
    parts = _KEEPING_ENDINGS.split(block.body)
    for heading in read_outline(block.body, block.body_start_line):
        parts[2 * (heading.line - block.body_start_line)] = _without_list(heading)
    return "".join(parts)


def _without_list(heading: Heading) -> str:
    """Take the list off a heading's raw line, after checking it.

    Args:
        heading: A real heading of the body.

    Returns:
        The raw line without its directive list.

    Raises:
        TemplateDirectiveError: The list is wrong.
    """
    try:
        read_directive_heading(heading.raw)
    except DirectiveSyntaxError as error:
        raise TemplateDirectiveError(
            error.message, error.column, heading.line
        ) from error
    return remove_directive_list(heading.raw)
