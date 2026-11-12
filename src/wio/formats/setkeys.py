# SPDX-License-Identifier: Apache-2.0
"""Setting keys in the metadata block of a contract."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


def set_block_keys(
    text: str,
    keys: Mapping[str, object],
    tables: Mapping[str, Mapping[str, object]] | None = None,
) -> str:
    """Set plain keys and tables in the metadata block of a text.

    It is the one function that edits the block of a contract, so no second editor
    of the block exists. It changes the block and nothing else: the form of the
    block, its other keys and their comments, the body and a leading byte-order
    mark stay as they were. It reads no file, and `tomlkit` is imported on the first
    call, not when `wio.formats` is imported. The keys of the block are plain keys,
    tables and inline tables; dotted keys are not supported.

    A key that the block already has is replaced in place, keeping its position,
    and so is a table that it already has, whose keys are set in the same way, each
    in place or added at the end of the table. The `id`, when the block has none,
    is put first as text, after `<!-- wio` or, for `+++` front matter, after the
    line `wio = 1`, and an `id` that is there is replaced in place.

    Any other plain key that the block lacks is added right after the last plain
    key, before the comment lines and the empty lines that follow it, or at the
    start of the block when it has no plain key, in the order given. A mapping in
    `keys` is written as an inline table with `tomlkit.inline_table()`, which is a
    plain key. A table that the block lacks is added after the last table, or after
    the plain keys when there is none, in the order given, separated from what
    precedes it by one empty line, which is added only when the block does not
    already end with one, and none for a block that is empty. A table that the
    block already has gains no empty line, so only an added table does.

    The key is placed by building the document again from the items of the parsed
    one with the public `append`, and not with `add`, which puts a new key after
    the comments and the empty lines that follow the last plain key. `append` gives
    a table that follows a key an empty line of its own, so the indent of each
    table that the block had is put back after it is appended. A block whose last
    line has no line ending is given one before it is parsed.

    The block is written with the line ending of its first line, or of the opening
    delimiter when the block is empty, so what is added has it and a block that
    mixed endings is written with it throughout, because `tomlkit` adds its own
    line feeds and the block is the one place that this function rewrites. The
    body, which follows the closing delimiter, is not touched.

    Args:
        text: The text of a contract, whose first line starts a metadata block of
            the form `<!-- wio` or `+++`.
        keys: The plain keys to set, in order, each with a value that TOML can
            write: a string, a number, a boolean, an array of them, or a mapping of
            them, which is written as an inline table. A mapping inside an array is
            not supported.
        tables: The tables to set, in order, each as the name of the table and the
            keys it holds.

    Returns:
        The text with the keys and the tables set.

    Raises:
        MetadataBlockError: The text has no metadata block, or its block cannot be
            read, as the block reader says.
        ValueError: A table is named like a plain key that the block has, or a plain
            key like a table that it has.
    """
    raise NotImplementedError
