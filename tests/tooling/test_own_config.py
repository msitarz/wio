# SPDX-License-Identifier: Apache-2.0
"""Tests that this repository's own config passes the check that it declares."""

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.slow

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / ".agents" / "wio" / "config.toml"
SCRIPT = Path(sys.executable).parent / "wio"


def test_the_repository_config_passes_its_own_check() -> None:
    """AC-3: `wio config check` exits 0 with no error in this repository."""
    # Given the delivered tree

    # When `wio config check` runs in it
    done = subprocess.run(
        [str(SCRIPT), "config", "check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then it exits 0 and prints no diagnostic
    assert (done.returncode, done.stdout, done.stderr) == (
        0,
        "Config check passed!\n",
        "",
    )


def test_the_header_of_the_config_says_what_reads_it() -> None:
    """AC-3: the file no longer says that nothing reads it."""
    # Given the comment at the top of the config
    header = CONFIG.read_text(encoding="utf-8").split("\n\n", maxsplit=1)[0]

    # When it is read

    # Then it names the command that reads the file and does not say that nothing
    # does
    assert "`wio config` reads this file" in header
    assert "Nothing reads" not in header
