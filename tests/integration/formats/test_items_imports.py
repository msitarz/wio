# SPDX-License-Identifier: Apache-2.0
"""Tests of the items of a section that need a fresh interpreter."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.slow
def test_the_parser_loads_when_the_items_of_a_section_are_first_found() -> None:
    """AC-5: `wio.formats` imports no parser, and finding items does."""
    # Given a program that imports `wio.formats`, reads `sys.modules`, finds the
    # items of a section and reads `sys.modules` again, in a new process
    # When it runs
    # Then `markdown_it` is absent the first time and present the second
