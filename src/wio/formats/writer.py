# SPDX-License-Identifier: Apache-2.0
"""The one writer of TOML, the only reader of `tomlkit` in `src/wio`."""

from typing import TYPE_CHECKING

lazy import tomlkit

if TYPE_CHECKING:
    from collections.abc import Mapping


def encode_toml(data: Mapping[str, object]) -> str:
    """Encode plain data as a TOML document.

    The keys that hold a value come first in the order given, then each table
    with its own keys in the order given, so a table never splits the keys of
    its parent. It writes no file and no comment. It loads `tomlkit` on the
    first call, not on import.

    Whatever `decode_toml` returns is written so that decoding it again gives
    the same data: strings, integers, floats, booleans, dates and times, arrays,
    tables and arrays of tables.

    Args:
        data: The document as nested mappings, lists and scalars, the shape
            that `decode_toml` returns.

    Returns:
        The document with LF line endings, ending in a line ending, and empty
        for an empty mapping.
    """
    return tomlkit.dumps(data)
