# SPDX-License-Identifier: Apache-2.0
"""Pure codecs between text and the shared types."""

lazy from wio.formats.block import read_metadata_block
lazy from wio.formats.diagnostics import render_json, render_text
lazy from wio.formats.errors import MetadataBlockError, TomlSyntaxError
lazy from wio.formats.toml import decode_toml

__all__ = [
    "MetadataBlockError",
    "TomlSyntaxError",
    "decode_toml",
    "read_metadata_block",
    "render_json",
    "render_text",
]
