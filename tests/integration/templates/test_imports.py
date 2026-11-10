# SPDX-License-Identifier: Apache-2.0
"""Tests of what `wio templates list` and `check` import, in a fresh interpreter."""

import ast
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "tests" / "fixtures" / "templates" / "check-pass"
NAMES = ("tomlkit", "json", "markdown_it")
_PROBE = """
import sys
from wio.cli import main
from wio.io.adapters import SystemStdio
names = ("tomlkit", "json", "markdown_it")
codes, loaded = [], []
for view in ("list", "check"):
    codes.append(main(["templates", view], SystemStdio()))
    loaded.append([name in sys.modules for name in names])
sys.stderr.write(repr([codes, loaded]))
"""


def _run(tmp_path: Path) -> tuple[list[int], list[list[bool]]]:
    """Run `list` and then `check` in one new process, in a project.

    Args:
        tmp_path: A directory to make the repository in.

    Returns:
        The two exit codes, and for each run whether each of `tomlkit`, `json` and
        `markdown_it` was in `sys.modules` after it.
    """
    project = tmp_path / "project"
    shutil.copytree(PROJECT, project)
    subprocess.run(["git", "init", "--quiet"], cwd=project, check=True)
    done = subprocess.run(
        [sys.executable, "-c", _PROBE],
        cwd=project,
        capture_output=True,
        text=True,
        check=True,
    )
    codes, loaded = ast.literal_eval(done.stderr)
    return codes, loaded


@pytest.mark.slow
def test_listing_and_checking_load_no_writer_and_no_json(tmp_path: Path) -> None:
    """Parent AC-2: `list` loads none of the three, `check` neither tomlkit nor json."""
    # Given a new Python process and a repository with valid templates

    # When `main(["templates", "list"], stdio)` and then
    # `main(["templates", "check"], stdio)` run in that process and `sys.modules`
    # is read after each
    codes, (after_list, after_check) = _run(tmp_path)

    # Then after the first none of the three modules is there, and after the
    # second neither `tomlkit` nor `json` is there
    assert codes == [0, 0]
    assert dict(zip(NAMES, after_list, strict=True)) == {
        "tomlkit": False,
        "json": False,
        "markdown_it": False,
    }
    assert (after_check[0], after_check[1]) == (False, False)
