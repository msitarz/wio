# SPDX-License-Identifier: Apache-2.0
"""Tests of the metadata block reader that need a fresh interpreter."""

import subprocess
import sys

import pytest

_PROBE = """
import sys
from wio.formats import read_metadata_block
read_metadata_block("# Title\\n")
read_metadata_block("+++\\nid = 1\\n+++\\n")
sys.stdout.write(str("tomllib" in sys.modules))
"""


@pytest.mark.slow
def test_reading_an_unmarked_text_does_not_import_tomllib() -> None:
    """AC-6: a text with no block loads no TOML decoder."""
    # Given a program that reads two unmarked texts in a new Python process
    # When it runs
    done = subprocess.run(
        [sys.executable, "-c", _PROBE], capture_output=True, text=True, check=True
    )

    # Then `tomllib` is not among the modules it holds
    assert done.stdout == "False"
