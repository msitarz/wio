# SPDX-License-Identifier: Apache-2.0
"""Tests for the installed `wio` command."""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.slow
@pytest.mark.xfail(
    strict=True,
    raises=(AssertionError, FileNotFoundError),
    reason="the wiring stage installs the command and the implementation stage "
    "makes it run",
)
def test_the_installed_command_exits_zero_without_output() -> None:
    """Running `wio` with no arguments succeeds silently, for now."""
    # Given the console script installed next to the Python executable
    script = Path(sys.executable).parent / "wio"

    # When it runs with no arguments
    result = subprocess.run([str(script)], capture_output=True, text=True, check=False)

    # Then it exits 0 and writes nothing
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
