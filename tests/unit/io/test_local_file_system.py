# SPDX-License-Identifier: Apache-2.0
"""Tests for `LocalFileSystem`, the adapter of the `FileSystem` port."""

import pytest


def test_reading_returns_text_as_stored_and_bytes_and_rejects_bad_utf8() -> None:
    """AC-2: reads keep line ends, and text that is not UTF-8 raises."""
    # Given a directory with a UTF-8 file and a file that is not valid UTF-8

    # When read_text and read_bytes run on them

    # Then the text keeps its line end, the bytes are returned, and bad text raises
    pytest.skip("stub: implemented with the adapter")


def test_writing_creates_parents_and_appending_adds_to_the_file() -> None:
    """AC-2: a write creates parent directories, and an append extends the file."""
    # Given a directory without a subdirectory

    # When write_text and then append_text run on a path inside it

    # Then the file holds both texts and the existence checks answer for each path
    pytest.skip("stub: implemented with the adapter")


def test_listing_is_sorted_and_missing_paths_raise() -> None:
    """AC-2: list_dir is sorted and the errors are the ones the port names."""
    # Given a directory with three entries, a file and a missing path

    # When list_dir runs on each and read_text runs on the missing path

    # Then the listing is sorted and the file and the missing path raise
    pytest.skip("stub: implemented with the adapter")
