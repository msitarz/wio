# SPDX-License-Identifier: Apache-2.0
"""Tests of the TOML writer in `wio.formats`."""

import datetime

from wio.formats import decode_toml, encode_toml


def test_the_writer_puts_the_keys_before_the_tables_in_the_order_given() -> None:
    """Skeleton AC-3: plain keys first, then each table with its own keys."""
    # Given a mapping with a key, a table and a second key written after it
    data = {"a": 1, "t": {"x": 1, "u": {"y": 2}}, "b": 2}

    # When it is encoded
    text = encode_toml(data)

    # Then both keys come first in order and the table follows with its keys
    assert text == "a = 1\nb = 2\n\n[t]\nx = 1\n\n[t.u]\ny = 2\n"


def test_the_writer_gives_nothing_for_an_empty_mapping() -> None:
    """Skeleton AC-4: no data is no text, so an empty block is its marks."""
    # Given an empty mapping
    # When it is encoded
    text = encode_toml({})

    # Then the text is empty
    assert text == ""


def test_what_the_decoder_returns_is_written_so_that_it_decodes_again() -> None:
    """Skeleton AC-1: strings, numbers, dates, arrays and tables round-trip."""
    # Given a mapping that holds every kind of value `decode_toml` returns, and
    # a table inside a table
    data: dict[str, object] = {
        "s": 'a "quoted" \\ string',
        "i": 3,
        "f": 1.5,
        "b": True,
        "dt": datetime.datetime(2020, 1, 2, 3, 4, 5),
        "d": datetime.date(2020, 1, 2),
        "t": datetime.time(3, 4, 5),
        "array": [1, 2, 3],
        "table": {"x": 1, "inner": {"y": [1, 2]}},
        "rows": [{"k": 1}, {"k": 2}],
    }

    # When it is encoded and the text is decoded
    again = decode_toml(encode_toml(data))

    # Then the data is equal to the mapping
    assert again == data
