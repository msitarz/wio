# SPDX-License-Identifier: Apache-2.0
"""Setting keys in the metadata block of a contract."""

import re
from collections.abc import Mapping
from difflib import SequenceMatcher
from typing import TYPE_CHECKING, cast

lazy import tomlkit
lazy from tomlkit.items import Table

from wio.formats.block import read_metadata_block
from wio.formats.errors import MetadataBlockError

if TYPE_CHECKING:
    from tomlkit.items import Comment
    from tomlkit.toml_document import TOMLDocument


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
    block = read_metadata_block(text)
    if block is None:
        msg = "The text has no metadata block"
        raise MetadataBlockError(msg, 1)
    start = text.index("\n") + 1
    end = _block_end(text, start, block.form)
    original = text[start:end]
    document = tomlkit.parse(original)
    _set_keys(document, keys)
    _set_tables(document, tables or {})
    ending = "\r\n" if text[:start].endswith("\r\n") else "\n"
    return (
        text[:start]
        + _restore_endings(original, document.as_string(), ending)
        + text[end:]
    )


def _block_end(text: str, start: int, form: str) -> int:
    """Find the closing delimiter's start after a validated opening.

    Args:
        text: The complete text.
        start: The first position inside the block.
        form: The validated block form.

    Returns:
        The position of the closing delimiter.

    Raises:
        MetadataBlockError: A front matter delimiter is absent.
    """
    if form == "comment":
        return text.index("-->", start)
    close = re.search(r"(?m)^\+\+\+[ \t]*\r?$", text[start:])
    if close is None:
        msg = "The metadata block does not close"
        raise MetadataBlockError(msg, 1)
    return start + close.start()


def _set_keys(document: TOMLDocument, keys: Mapping[str, object]) -> None:
    """Set plain keys, refusing to replace a table with one.

    Args:
        document: The parsed block to change.
        keys: The plain keys and values.

    Raises:
        ValueError: A requested name is already a table.
    """
    for name, value in keys.items():
        if name in document and isinstance(document.item(name), Table):
            msg = f"`{name}` is a table"
            raise ValueError(msg)
        document[name] = _inline(value)


def _set_tables(
    document: TOMLDocument, tables: Mapping[str, Mapping[str, object]]
) -> None:
    """Set tables, refusing to replace a plain key with one.

    Args:
        document: The parsed block to change.
        tables: The tables and their values.

    Raises:
        ValueError: A requested name is already a plain key.
    """
    for name, values in tables.items():
        _set_table(document, name, values)


def _set_table(document: TOMLDocument, name: str, values: Mapping[str, object]) -> None:
    """Replace or add one table, retaining its existing comments.

    Args:
        document: The parsed block to change.
        name: The table name.
        values: The table's new values.

    Raises:
        ValueError: The name is already a plain key.
    """
    previous = document.item(name) if name in document else None
    if previous is not None and not isinstance(previous, Table):
        msg = f"`{name}` is a plain key"
        raise ValueError(msg)
    table = tomlkit.table()
    for key, value in values.items():
        table.add(key, _inline(value))
    if isinstance(previous, Table):
        _preserve_comments(previous, table)
    document[name] = table


def _preserve_comments(previous: Table, replacement: Table) -> None:
    """Carry comments from a replaced table into its replacement.

    Args:
        previous: The existing table and its comments.
        replacement: The new table, to which comments are added.
    """
    replacement.trivia.comment = previous.trivia.comment
    replacement.trivia.comment_ws = previous.trivia.comment_ws
    for comment in _table_comments(previous):
        item = tomlkit.parse(comment + "\n").body[0][1]
        replacement.add(cast("Comment", item))


def _table_comments(table: Table) -> list[str]:
    """Collect comments on a table's entries, including nested tables.

    Args:
        table: The table whose entries may carry comments.

    Returns:
        The comment text in its original order.
    """
    comments: list[str] = []
    for _, item in table.value.body:
        if item.trivia.comment:
            comments.append(item.trivia.comment)
        if isinstance(item, Table):
            comments.extend(_table_comments(item))
    return comments


def _inline(value: object) -> object:
    """Convert nested mappings to TOML inline tables.

    Args:
        value: A value to write.

    Returns:
        A value accepted by tomlkit, with mappings made inline.
    """
    if isinstance(value, Mapping):
        table = tomlkit.inline_table()
        for key, member in value.items():
            table.add(str(key), _inline(member))
        return table
    if isinstance(value, (list, tuple)):
        array = tomlkit.array()
        for member in value:
            array.append(_inline(member))
        return array
    return value


def _restore_endings(original: str, edited: str, ending: str) -> str:
    """Preserve the endings of unchanged lines and give added lines an ending.

    Args:
        original: The original TOML block.
        edited: The edited TOML block.
        ending: The ending for added lines.

    Returns:
        The edited block with its line endings restored.
    """
    old = original.splitlines(keepends=True)
    new = edited.splitlines(keepends=True)
    matcher = SequenceMatcher(None, list(map(_clean, old)), list(map(_clean, new)))
    endings = _matched_endings(old, matcher)
    return "".join(
        _clean(line) + endings.get(i, ending if line.endswith("\n") else "")
        for i, line in enumerate(new)
    )


def _matched_endings(old: list[str], matcher: SequenceMatcher[str]) -> dict[int, str]:
    """Find existing line endings for unchanged or replaced lines.

    Args:
        old: The original lines with their endings.
        matcher: The comparison of old and new line contents.

    Returns:
        The existing endings keyed by their new line indexes.
    """
    endings: dict[int, str] = {}
    for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if (
            tag not in {"equal", "replace"}
            or old_end - old_start != new_end - new_start
        ):
            continue
        for i, j in zip(
            range(old_start, old_end), range(new_start, new_end), strict=True
        ):
            endings[j] = old[i][len(_clean(old[i])) :]
    return endings


def _clean(line: str) -> str:
    """Remove a line ending while keeping the line's contents.

    Args:
        line: A line with or without its ending.

    Returns:
        The line without its LF or CRLF ending.
    """
    return line.removesuffix("\n").removesuffix("\r")
