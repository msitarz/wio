# SPDX-License-Identifier: Apache-2.0
"""Tests of the items of a section that need a fresh interpreter."""

import json
import subprocess
import sys

import pytest

_PROBE = """
import json, sys
import wio.formats
from wio.formats import read_outline
before = "markdown_it" in sys.modules
body = "## Goals\\n\\n- one\\n"
heading = read_outline(body, 1)[0]
wio.formats.find_items(body, 1, heading, ())
sys.stdout.write(json.dumps([before, "markdown_it" in sys.modules]))
"""


@pytest.mark.slow
def test_the_parser_loads_when_the_items_of_a_section_are_first_found() -> None:
    """AC-5: `wio.formats` imports no parser, and finding items does."""
    # Given a program that imports `wio.formats`, reads `sys.modules`, finds the
    # items of a section and reads `sys.modules` again, in a new process
    # When it runs
    done = subprocess.run(
        [sys.executable, "-c", _PROBE], capture_output=True, text=True, check=True
    )

    # Then `markdown_it` is absent the first time and present the second
    assert json.loads(done.stdout) == [False, True]
