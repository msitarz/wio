# SPDX-License-Identifier: Apache-2.0
"""Tests for the installed `wio` command."""

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(sys.executable).parent / "wio"


@pytest.mark.slow
def test_the_console_script_is_installed() -> None:
    """Synchronizing the environment installs the `wio` command."""
    # Given the environment the tests run in

    # When the console script is looked for next to the Python executable
    found = SCRIPT.is_file()

    # Then it is there
    assert found


@pytest.mark.slow
@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="the implementation stage binds the streams the command runs on",
)
def test_the_installed_command_exits_zero_without_output() -> None:
    """Running `wio` with no arguments succeeds silently, for now."""
    # Given the installed console script

    # When it runs with no arguments
    result = subprocess.run([str(SCRIPT)], capture_output=True, text=True, check=False)

    # Then it exits 0 and writes nothing
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
