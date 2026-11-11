# SPDX-License-Identifier: Apache-2.0
"""Tests of what `wio contracts` imports, in a fresh interpreter."""

import ast
import subprocess
import sys

import pytest

_PROBE = """
import sys
from wio.cli import main
from wio.io.adapters import SystemStdio
code = main(["contracts"], SystemStdio())
names = ("tomlkit", "json", "markdown_it")
sys.stderr.write(repr([code, [name in sys.modules for name in names]]))
"""


@pytest.mark.slow
def test_bare_contracts_loads_no_codec() -> None:
    """AC-1: `tomlkit`, `json` and `markdown_it` stay unloaded."""
    # Given a new Python process

    # When `main(["contracts"], stdio)` of `wio.cli` runs and `sys.modules` is read
    done = subprocess.run(
        [sys.executable, "-c", _PROBE], capture_output=True, text=True, check=True
    )
    code, loaded = ast.literal_eval(done.stderr)

    # Then none of `tomlkit`, `json` and `markdown_it` is there
    assert (code, loaded) == (0, [False, False, False])
