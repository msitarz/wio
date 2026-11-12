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
    uses `tomlkit` to edit the block. Key placement and spacing within it may
    change; untouched values and comments are retained. A table that already
    exists is replaced by the table given, not merged. A mapping in `keys` is
    written as an inline table, which is a plain key.

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
