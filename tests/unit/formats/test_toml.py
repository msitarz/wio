# SPDX-License-Identifier: Apache-2.0
"""Tests of the TOML decoder in `wio.formats`."""

import pytest

from wio.errors import WioError
lazy from wio.formats import TomlSyntaxError, decode_toml


def test_a_toml_text_becomes_plain_data() -> None:
    """AC-1: a valid document is nested dicts, lists and scalars."""
    # Given a document with a key, a table, a string and a list, and an empty text
    text = 'a = 1\n[t]\ns = "x"\nl = [1, 2]\n'

    # When decode_toml runs on each
    data = decode_toml(text)
    empty = decode_toml("")

    # Then the document is returned as written, and the empty text gives {}
    assert data == {"a": 1, "t": {"s": "x", "l": [1, 2]}}
    assert empty == {}


def test_an_invalid_value_carries_its_position() -> None:
    """AC-2: a syntax error is a WioError with a message, a line and a column."""
    # Given a text whose second line is an invalid value
    text = "a = 1\nb = = 2\n"

    # When decode_toml runs
    with pytest.raises(TomlSyntaxError) as caught:
        decode_toml(text)

    # Then the error is a WioError at line 2, column 5, and str holds all three
    error = caught.value
    assert isinstance(error, WioError)
    assert (error.line, error.column) == (2, 5)
    assert error.message
    assert str(error) == f"{error.message} (line 2, column 5)"


@pytest.mark.parametrize(
    ("text", "position"),
    [("a = 1\na = 2\n", (2, 6)), ('a = "x', (1, 7))],
)
def test_a_duplicate_key_and_an_unterminated_string_are_placed(
    text: str, position: tuple[int, int]
) -> None:
    """AC-2: the position is the problem's, not the start of the text."""
    # Given a text with a duplicate key, or an unterminated string

    # When decode_toml runs on it
    with pytest.raises(TomlSyntaxError) as caught:
        decode_toml(text)

    # Then the error is at the position of the problem
    assert (caught.value.line, caught.value.column) == position
