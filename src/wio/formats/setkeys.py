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
    plain key, which is the last line before the first table that is not a comment
    line or an empty line, so before the comment lines and the empty lines that
    follow it, or at the start of the block when it has no plain key, in the order
    given. A mapping in `keys` is written as an inline table, which is a plain key.
    A table that the block lacks is added at the end of the block, after the last
    table or after the plain keys, in the order given, with one empty line before
    it, which is added only when the block does not already end with one and is
    left out for a block that is empty. A block whose last line has no line ending
    is given one first. Only an added table adds an empty line, and a table that
    the block already has gains none.

    The block is written with the line ending of the line of its opening
    delimiter: its text is read with line feeds, edited, and written back with that
    ending, so a block that mixed endings is written with one, and the body is not
    touched. Dotted keys are not supported. The scan for the last plain key takes a
    comment or empty line that ends a multi-line string for one that ends the key.

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
        ValueError: The function itself refuses a table that is named like a plain
            key of the block, a plain key named like a table of the block, and a
            mapping inside an array.
    """
    raise NotImplementedError
