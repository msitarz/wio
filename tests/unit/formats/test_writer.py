# SPDX-License-Identifier: Apache-2.0
"""Tests of the TOML writer in `wio.formats`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_writer_puts_the_keys_before_the_tables_in_the_order_given() -> None:
    """AC-3 of the skeleton: scalars first, then each table with its own keys."""
    # Given a mapping with a key, a table and a second key written after it
    # When it is encoded
    # Then both keys come first in order and the table follows with its keys


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_the_writer_gives_nothing_for_an_empty_mapping() -> None:
    """AC-4 of the skeleton: no data is no text, so an empty block is its marks."""
    # Given an empty mapping
    # When it is encoded
    # Then the text is empty
