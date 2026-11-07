# SPDX-License-Identifier: Apache-2.0
"""Pure codecs between text and the shared types."""

lazy from wio.formats.errors import TomlSyntaxError
lazy from wio.formats.toml import decode_toml

__all__ = ["TomlSyntaxError", "decode_toml"]
