# SPDX-License-Identifier: Apache-2.0
"""Tests of the TOML decoder in `wio.formats` that need a fresh interpreter."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]

_PROBE = """
import json, sys
import wio.formats
before = "tomllib" in sys.modules
wio.formats.decode_toml("a = 1")
sys.stdout.write(json.dumps([before, "tomllib" in sys.modules]))
"""


@pytest.mark.slow
def test_importing_the_decoder_loads_no_toml_parser() -> None:
    """AC-4: `tomllib` loads on the first decode, not on import."""
    # Given a new Python process

    # When it imports wio.formats, checks sys.modules, decodes, and checks again
    done = subprocess.run(
        [sys.executable, "-c", _PROBE],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    # Then tomllib is absent the first time and present the second
    assert json.loads(done.stdout) == [False, True]
