# SPDX-License-Identifier: Apache-2.0
"""Tests of the outline that need a fresh interpreter."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.slow
def test_the_parser_loads_when_the_outline_first_reads_a_body() -> None:
    """AC-6: `wio.formats` imports no parser, and the first reading does."""
    # Given a program that imports `wio.formats`, reads `sys.modules`, reads one
    # body with the outline and reads `sys.modules` again, in a new process
    # When it runs
    # Then `markdown_it` is absent the first time and present the second
