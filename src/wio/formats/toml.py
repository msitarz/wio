# SPDX-License-Identifier: Apache-2.0
"""The decoder of TOML text, the only reader of `tomllib` in `src/wio`."""

lazy import tomllib

from wio.formats.errors import TomlSyntaxError


def decode_toml(text: str) -> dict[str, object]:
    """Decode a TOML document into plain Python data.

    Tables become `dict`s and arrays `list`s, with every table and key as
    written. It reads no file and keeps no comment. It loads `tomllib` on the
    first call, not on import.

    Args:
        text: The TOML document.

    Returns:
        The document as nested `dict`s, `list`s and scalars. An empty text gives
        an empty `dict`.

    Raises:
        TomlSyntaxError: The text is not valid TOML. It carries the line and
            column of the first problem, and no file name.
    """
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise TomlSyntaxError(error.msg, error.lineno, error.colno) from error
