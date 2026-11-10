# SPDX-License-Identifier: Apache-2.0
"""Tests of the TOML writer in `wio.formats`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_writer_puts_the_keys_before_the_tables_in_the_order_given() -> None:
    """Skeleton AC-3: plain keys first, then each table with its own keys."""
    # Given a mapping with a key, a table and a second key written after it
    # When it is encoded
    # Then both keys come first in order and the table follows with its keys


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_writer_gives_nothing_for_an_empty_mapping() -> None:
    """Skeleton AC-4: no data is no text, so an empty block is its marks."""
    # Given an empty mapping
    # When it is encoded
    # Then the text is empty


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_what_the_decoder_returns_is_written_so_that_it_decodes_again() -> None:
    """Skeleton AC-1: strings, numbers, dates, arrays and tables round-trip."""
    # Given a mapping that holds every kind of value `decode_toml` returns, and
    # a table inside a table
    # When it is encoded and the text is decoded
    # Then the data is equal to the mapping
