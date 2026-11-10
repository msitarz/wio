# SPDX-License-Identifier: Apache-2.0
"""Pure codecs between text and the shared types."""

lazy from wio.formats.block import read_metadata_block
lazy from wio.formats.diagnostics import render_json, render_text
lazy from wio.formats.directives import (
    COMBINING,
    DIRECTIVES,
    read_directive_heading,
    remove_directive_list,
)
lazy from wio.formats.errors import (
    DirectiveSyntaxError,
    MetadataBlockError,
    NotATemplateError,
    TemplateDirectiveError,
    TomlSyntaxError,
)
lazy from wio.formats.outline import read_outline
lazy from wio.formats.skeleton import prepare_skeleton
lazy from wio.formats.toml import decode_toml
lazy from wio.formats.writer import encode_toml

__all__ = [
    "COMBINING",
    "DIRECTIVES",
    "DirectiveSyntaxError",
    "MetadataBlockError",
    "NotATemplateError",
    "TemplateDirectiveError",
    "TomlSyntaxError",
    "decode_toml",
    "encode_toml",
    "prepare_skeleton",
    "read_directive_heading",
    "read_metadata_block",
    "read_outline",
    "remove_directive_list",
    "render_json",
    "render_text",
]
