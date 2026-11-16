# SPDX-License-Identifier: Apache-2.0
"""Tests of the shared JSON encoder."""

from wio.formats import encode_json


def test_json_encoding_preserves_default_and_config_formats() -> None:
    """The encoder retains the formats used by commands."""
    # Given a value with non-ASCII text and a nested array
    value = {"name": "é", "items": [1, 2]}

    # When it is encoded with default and config options
    compact = encode_json(value)
    indented = encode_json(value, indent=2, ensure_ascii=False)

    # Then spacing, escaping and the absence of a trailing newline are retained
    assert compact == '{"name": "\\u00e9", "items": [1, 2]}'
    assert indented == '{\n  "name": "é",\n  "items": [\n    1,\n    2\n  ]\n}'
