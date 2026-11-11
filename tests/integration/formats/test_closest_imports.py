# SPDX-License-Identifier: Apache-2.0
"""Tests of the closest key that need a fresh interpreter."""

import ast
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "tests" / "fixtures" / "templates" / "check-pass"
_PROBE = """
import sys
import wio.formats
from wio.cli import main
from wio.io.adapters import SystemStdio
names = ("difflib", "json")
before = [name in sys.modules for name in names]
codes = [main([command, "check"], SystemStdio()) for command in ("config", "templates")]
checked = [name in sys.modules for name in names]
wio.formats.closest_key("descriptions", ("description",))
after = [name in sys.modules for name in names]
sys.stderr.write(repr([codes, before, checked, after]))
"""


@pytest.mark.slow
def test_difflib_and_json_load_only_when_they_are_needed(tmp_path: Path) -> None:
    """AC-3: no import at start, nor in a run that finds no mistyped key."""
    # Given a new process, a valid config and valid templates
    project = tmp_path / "project"
    shutil.copytree(PROJECT, project)
    subprocess.run(["git", "init", "--quiet"], cwd=project, check=True)

    # When `wio.formats` is imported, the config and templates checks run in text
    # form, `sys.modules` is read, then `closest_key` is called and it is read
    # again
    done = subprocess.run(
        [sys.executable, "-c", _PROBE],
        cwd=project,
        capture_output=True,
        text=True,
        check=True,
    )
    codes, before, checked, after = ast.literal_eval(done.stderr)

    # Then neither `difflib` nor `json` is there the first time, and `difflib` is
    # there the second
    assert codes == [0, 0]
    assert before == [False, False]
    assert checked == [False, False]
    assert after == [True, False]
