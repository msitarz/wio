# SPDX-License-Identifier: Apache-2.0
"""Tests of the outline that need a fresh interpreter."""

import json
import subprocess
import sys

import pytest

_PROBE = """
import json, sys
import wio.formats
before = "markdown_it" in sys.modules
wio.formats.read_outline("# Title\\n", 1)
sys.stdout.write(json.dumps([before, "markdown_it" in sys.modules]))
"""


@pytest.mark.slow
def test_the_parser_loads_when_the_outline_first_reads_a_body() -> None:
    """AC-6: `wio.formats` imports no parser, and the first reading does."""
    # Given a program that imports `wio.formats`, reads `sys.modules`, reads one
    # body with the outline and reads `sys.modules` again, in a new process

    # When it runs
    done = subprocess.run(
        [sys.executable, "-c", _PROBE], capture_output=True, text=True, check=True
    )

    # Then `markdown_it` is absent the first time and present the second
    assert json.loads(done.stdout) == [False, True]
