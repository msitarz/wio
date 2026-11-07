# SPDX-License-Identifier: Apache-2.0
"""Tests for the installed `wio` command."""

import importlib.metadata
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
def test_the_installed_command_shows_the_version() -> None:
    """Running `wio --version` prints the version of the distribution."""
    # Given the installed console script

    # When it runs with --version
    result = subprocess.run(
        [str(SCRIPT), "--version"], capture_output=True, text=True, check=False
    )

    # Then it exits 0 and prints wio and the version
    version = importlib.metadata.version("work-it-out")
    assert (result.returncode, result.stdout, result.stderr) == (
        0,
        f"wio {version}\n",
        "",
    )
