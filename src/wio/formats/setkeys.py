# SPDX-License-Identifier: Apache-2.0
"""Rewriting the metadata block of a contract."""

import re
from typing import TYPE_CHECKING

from wio.formats.block import read_metadata_block
from wio.formats.errors import MetadataBlockError
from wio.formats.writer import encode_toml

if TYPE_CHECKING:
    from collections.abc import Mapping


def set_block_keys(
    text: str,
    keys: Mapping[str, object],
    tables: Mapping[str, Mapping[str, object]] | None = None,
) -> str:
    """Set keys and tables, rewriting metadata while preserving the body.

    TOML comments and formatting are discarded. When supplied, `id` is first,
    after the front matter marker. Other values, delimiters and the body are
    retained. Rewritten lines use the opening line ending.

    Args:
        text: Text beginning with a metadata block.
        keys: Keys and their replacement values.
        tables: Tables and their replacement values.

    Returns:
        Text with the requested metadata values.

    Raises:
        MetadataBlockError: The text has no valid metadata block.
    """
    block = read_metadata_block(text)
    if block is None:
        msg = "The text has no metadata block"
        raise MetadataBlockError(msg, 1)
    start = text.index("\n") + 1
    end = _block_end(text, start, block.form)
    values = dict(block.data)
    values.update(keys)
    values.update(tables or {})
    ordered: dict[str, object] = {}
    if block.form == "front-matter":
        ordered["wio"] = block.version
    if "id" in keys:
        ordered["id"] = values.pop("id")
    ordered.update(values)
    ending = "\r\n" if text[:start].endswith("\r\n") else "\n"
    encoded = encode_toml(ordered)
    if block.form == "comment":
        encoded = encoded.replace("-->", r"--\u003e")
    return text[:start] + encoded.replace("\n", ending) + text[end:]


def _block_end(text: str, start: int, form: str) -> int:
    """Find the closing delimiter after a validated opening.

    Args:
        text: The complete text.
        start: The first position inside the block.
        form: The metadata block form.

    Returns:
        The closing delimiter's position.
    """
    if form == "comment":
        return text.index("-->", start)
    close = re.search(r"(?m)^\+\+\+[ \t]*\r?$", text[start:])
    assert close is not None
    return start + close.start()
