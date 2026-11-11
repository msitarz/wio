# SPDX-License-Identifier: Apache-2.0
"""Tests of where the items of a section are found."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_only_wio_formats_imports_the_parser_and_exports_the_items() -> None:
    """AC-6: `wio.formats` exports the finder and the judge of items."""
    # Given the sources of `src/wio`
    # When their syntax trees are searched for the imports of `markdown_it` and
    # for the exports of `wio.formats`
    # Then only modules of `wio.formats` import `markdown_it`, and `wio.formats`
    # exports the finder and the judge
