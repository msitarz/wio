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
    of the block exists. It edits the text of the block, which lies between the
    opening delimiter and the closing one, and nothing else: the body, a leading
    byte-order mark and the delimiters stay as they were. It reads no file, and
    `tomlkit` is imported on the first call, not when `wio.formats` is imported. It
    uses `tomlkit` to read the block, to replace a value where it stands, and to
    write a value, and it places the lines that it adds itself, as text, so that
    nothing else of the block moves.

    A key that the block already has is replaced in place, keeping its position
    and the comment on its line. A table that it already has is replaced in place
    by the table that was given, which is not merged with it. The `id`, when the
    block has none, is put first as a line of text, after the opening delimiter or,
    for `+++` front matter, after the line `wio = 1`.

    Any other plain key that the block lacks is added as a line after the last
    plain key, including all lines of a multiline value, so before the comment
    lines and empty lines that follow it, or at the start of the block when it has
    no plain key, in the order given. A mapping in `keys` is written as an inline
    table, which is a plain key.
    A table that the block lacks is added at the end of the block, after the last
    table or after the plain keys, in the order given, with one empty line before
    it, which is added only when the block does not already end with one and is
    left out for a block that is empty. A block whose last line has no line ending
    is given one first. Only an added table adds an empty line, and a table that
    the block already has gains none.

    Added lines use the line ending of the opening delimiter. Existing line endings
    are preserved, even in a block with mixed endings. Dotted keys and multiline
    values already in the block are preserved.

    Args:
        text: The text of a contract, whose first line starts a metadata block of
            the form `<!-- wio` or `+++`.
        keys: The plain keys to set, in order, each with a value that TOML can
            write, including arrays and mappings; a mapping is written as an
            inline table.
        tables: The tables to set, in order, each as the name of the table and the
            keys it holds.

    Returns:
        The text with the keys and the tables set.

    Raises:
        MetadataBlockError: The text has no metadata block, or its block cannot be
            read, as the block reader says.
        ValueError: The function itself refuses a table that is named like a plain
            key of the block or a plain key named like a table of the block.
    """
    raise NotImplementedError
