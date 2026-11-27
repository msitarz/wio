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
from wio.formats.writer import encode_comment_toml, encode_toml

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
    """Find the line ending that a skeleton's block is written with."""
    found = _LINE_ENDING.search(text)
    return "\r\n" if found is not None and found[0] == "\r\n" else "\n"


def _metadata(name: str, data: Mapping[str, object]) -> dict[str, object]:
    """Pick what a contract's metadata holds out of a template's metadata."""
    contract = data.get("contract")
    kept = (
        {key: value for key, value in contract.items() if key not in _DROPPED}
        if isinstance(contract, Mapping)
        else {}
    )
    return {"template": name, **kept}


def _write_block(form: BlockForm, data: Mapping[str, object], ending: str) -> str:
    """Write a metadata block of the given form."""
    if form == "comment":
        toml = encode_comment_toml(data).replace("\n", ending)
        return f"<!-- wio{ending}{toml}-->{ending}"
    toml = encode_toml(data).replace("\n", ending)
    return f"+++{ending}wio = 1{ending}{toml}+++{ending}"


def _strip_lists(block: MetadataBlock) -> str:
    """Take the directive list off each real heading of a template's body."""
    parts = _KEEPING_ENDINGS.split(block.body)
    for heading in read_outline(block.body, block.body_start_line):
        parts[2 * (heading.line - block.body_start_line)] = _without_list(heading)
    return "".join(parts)


def _without_list(heading: Heading) -> str:
    """Take the list off a heading's raw line, after checking it."""
    try:
        read_directive_heading(heading.raw)
    except DirectiveSyntaxError as error:
        raise TemplateDirectiveError(
            error.message, error.column, heading.line
        ) from error
    return remove_directive_list(heading.raw)
