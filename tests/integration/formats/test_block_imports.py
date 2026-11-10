# SPDX-License-Identifier: Apache-2.0
"""Tests of the metadata block reader that need a fresh interpreter."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.slow
def test_reading_an_unmarked_text_does_not_import_tomllib() -> None:
    """AC-6: a text with no block loads no TOML decoder."""
    # Given a program that reads two unmarked texts in a new Python process
    # When it runs
    # Then `tomllib` is not among the modules it holds
