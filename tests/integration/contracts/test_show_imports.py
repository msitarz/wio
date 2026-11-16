# SPDX-License-Identifier: Apache-2.0
"""Tests of what `wio contracts show` imports, in a fresh interpreter."""

import ast
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from tests.sandbox import Sandbox

_PROBE = """
import sys
from wio.cli import main
from wio.io.adapters import SystemStdio
code = main(["contracts", "show", "k3m9xq"], SystemStdio())
names = ("tomlkit", "json")
sys.stderr.write(repr([code, [name in sys.modules for name in names]]))
"""
_WORK = '<!-- wio\nid = "k3m9xq"\n-->\n\n# Solo\n'


@pytest.mark.slow
def test_show_without_json_loads_neither_json_nor_tomlkit(sandbox: Sandbox) -> None:
    """AC-6: a run without `--json` leaves both unloaded."""
    # Given a new Python process and a repository with the Work of AC-6
    work = sandbox.root / ".agents/wio/works/s/README.md"
    work.parent.mkdir(parents=True)
    work.write_text(_WORK)
    (sandbox.root / ".agents/wio/config.toml").write_text("")
    subprocess.run(
        ["git", "init", "--quiet"], cwd=sandbox.root, env=sandbox.env, check=True
    )

    # When `main(["contracts", "show", "k3m9xq"], stdio)` of `wio.cli` runs and
    # `sys.modules` is read
    done = subprocess.run(
        [sys.executable, "-c", _PROBE],
        cwd=sandbox.root,
        env=sandbox.env,
        capture_output=True,
        text=True,
        check=True,
    )
    code, loaded = ast.literal_eval(done.stderr)

    # Then the Work was shown, and neither `tomlkit` nor `json` is there
    assert done.stdout.startswith("Work k3m9xq  Solo\n")
    assert (code, loaded) == (0, [False, False])
