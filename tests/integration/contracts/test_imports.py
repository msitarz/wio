# SPDX-License-Identifier: Apache-2.0
"""Tests of what `wio contracts list` and `check` import, in a fresh interpreter."""

import ast
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "tests" / "fixtures" / "contracts" / "check-clean"
_PROBE = """
import sys
from wio.cli import main
from wio.io.adapters import SystemStdio

def loaded():
    return [name in sys.modules for name in ("tomlkit", "json")]

first = main(["contracts", "list"], SystemStdio())
after_list = loaded()
second = main(["contracts", "check"], SystemStdio())
sys.stderr.write(repr([[first, second], [after_list, loaded()]]))
"""


@pytest.mark.slow
def test_listing_and_checking_load_no_writer_and_no_json(tmp_path: Path) -> None:
    """Parent AC-6: after `list` and after `check`, neither module is loaded."""
    # Given a new Python process and a repository with valid Works
    project = tmp_path / "project"
    shutil.copytree(PROJECT, project)
    subprocess.run(["git", "init", "--quiet"], cwd=project, check=True)

    # When `main(["contracts", "list"], stdio)` and then
    # `main(["contracts", "check"], stdio)` run in that process and `sys.modules`
    # is read after each
    done = subprocess.run(
        [sys.executable, "-c", _PROBE],
        cwd=project,
        capture_output=True,
        text=True,
        check=True,
    )
    codes, loaded = ast.literal_eval(done.stderr)

    # Then both succeeded, and after each neither `tomlkit` nor `json` is there
    assert codes == [0, 0]
    assert loaded == [[False, False], [False, False]]
