# SPDX-License-Identifier: Apache-2.0
"""Pure codecs between text and the shared types."""

lazy from wio.formats.block import read_metadata_block
lazy from wio.formats.closest import closest_key
lazy from wio.formats.diagnostics import (
    encode_json,
    render_check,
    render_json,
    render_text,
)
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
lazy from wio.formats.event_lines import Decoding, Entry, decode_lines, encode_line
lazy from wio.formats.items import find_items, judge_items
lazy from wio.formats.outline import read_outline
lazy from wio.formats.records import check_shape, read
lazy from wio.formats.rendering import render
lazy from wio.formats.setkeys import set_block_keys
lazy from wio.formats.skeleton import prepare_skeleton
lazy from wio.formats.toml import decode_toml
lazy from wio.formats.writer import encode_toml

__all__ = [
    "COMBINING",
    "DIRECTIVES",
    "Decoding",
    "DirectiveSyntaxError",
    "Entry",
    "MetadataBlockError",
    "NotATemplateError",
    "TemplateDirectiveError",
    "TomlSyntaxError",
    "check_shape",
    "closest_key",
    "decode_lines",
    "decode_toml",
    "encode_json",
    "encode_line",
    "encode_toml",
    "find_items",
    "judge_items",
    "prepare_skeleton",
    "read",
    "read_directive_heading",
    "read_metadata_block",
    "read_outline",
    "remove_directive_list",
    "render",
    "render_check",
    "render_json",
    "render_text",
    "set_block_keys",
]
