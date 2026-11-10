# SPDX-License-Identifier: Apache-2.0
"""Tests of the skeleton that need a fresh interpreter."""

import json
import subprocess
import sys

import pytest

_PROBE = """
import json, sys
import wio.formats
wio.formats.read_metadata_block('<!-- wio\\nkind = "k"\\n-->\\n')
before = "tomlkit" in sys.modules
wio.formats.prepare_skeleton("x", '<!-- wio\\nkind = "k"\\n-->\\n')
sys.stdout.write(json.dumps([before, "tomlkit" in sys.modules]))
"""


@pytest.mark.slow
def test_the_writer_loads_when_a_skeleton_is_first_prepared() -> None:
    """AC-6: importing `wio.formats` and reading a block load no writer."""
    # Given a program that imports `wio.formats`, reads a block, reads
    # `sys.modules`, prepares a skeleton and reads it again, in a new process
    # When it runs
    done = subprocess.run(
        [sys.executable, "-c", _PROBE], capture_output=True, text=True, check=True
    )

    # Then `tomlkit` is absent the first time and present the second
    assert json.loads(done.stdout) == [False, True]
