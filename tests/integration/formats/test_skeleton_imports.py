# SPDX-License-Identifier: Apache-2.0
"""Tests of the skeleton that need a fresh interpreter."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
@pytest.mark.slow
def test_the_writer_loads_when_a_skeleton_is_first_prepared() -> None:
    """AC-6: importing `wio.formats` and reading a block load no writer."""
    # Given a program that imports `wio.formats`, reads a block, reads
    # `sys.modules`, prepares a skeleton and reads it again, in a new process
    # When it runs
    # Then `tomlkit` is absent the first time and present the second
