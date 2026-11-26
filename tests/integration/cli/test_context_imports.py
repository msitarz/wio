# SPDX-License-Identifier: Apache-2.0
"""The modules a context run loads in a fresh interpreter."""

import ast
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.drivers.stub_known_work import (
    KnownWorkStubReachedError,
    identify_known_work_stub,
)
from tests.support import git

if TYPE_CHECKING:
    from tests.sandbox import Sandbox

_PROBE = """
import sys
from wio.cli import main
from wio.io.adapters import SystemStdio
code = main(["context", "k3m9xq", "deliver", "goal"], SystemStdio())
names = ("tomlkit", "wio.config.command", "wio.contracts.command",
         "wio.log.command", "wio.rules.command", "wio.templates.command",
         "wio.trailers.command")
sys.stderr.write(repr((code, [name for name in names if name in sys.modules])))
"""


@pytest.mark.slow
@pytest.mark.xfail(
    strict=True, raises=KnownWorkStubReachedError, reason="Work check is stubbed"
)
def test_context_run_does_not_load_unrelated_commands(sandbox: Sandbox) -> None:
    """C-6: composing a bundle leaves the named unrelated modules unloaded."""
    # Given a repository with a goal stage and a Work
    config = sandbox.root / ".agents/wio/config.toml"
    config.parent.mkdir(parents=True)
    config.write_text(
        '[works.defaults.actions]\ndeliver = ["goal"]\n'
        '[actions.deliver]\ndescription = "Deliver"\n'
        "[roots.api]\npaths = []\n"
        '[stages.goal]\ngoal = "Read the contract."\n'
    )
    work = sandbox.root / ".agents/wio/works/demo/README.md"
    work.parent.mkdir(parents=True)
    work.write_text('<!-- wio\nid = "k3m9xq"\nroots = ["api"]\n-->\n\n# Demo\n')
    git(sandbox, "init", "-q", check=True)

    # When the command runs in a fresh interpreter
    done = subprocess.run(
        [sys.executable, "-c", _PROBE],
        cwd=sandbox.root,
        env=sandbox.env,
        capture_output=True,
        text=True,
        check=True,
    )
    # Then a bundle was emitted without loading the unrelated modules
    error, _, summary = done.stderr.rpartition("\n")
    if error:
        code, _ = ast.literal_eval(summary)
        identify_known_work_stub(code, done.stdout, error + "\n")
    assert done.stdout.startswith("bundle: ")
    assert ast.literal_eval(done.stderr) == (0, [])
