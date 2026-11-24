# SPDX-License-Identifier: Apache-2.0
"""Scenarios of the rules and the config when a rules directory cannot be read.

They close real directories, so they run on the CLI channel, where the process
reads the disk, and not as root, who can read any directory.
"""

import os
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel
from tests.acceptance.rules.support import BASE, RULES, rule, ruleset
from tests.sandbox import unreadable

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox

pytestmark = [
    pytest.mark.channels(Channel.CLI),
    pytest.mark.skipif(os.geteuid() == 0, reason="root can read any directory"),
]
MANIFEST = '[families]\nARC = "A"\n'
DENIED = "The directory cannot be listed: Permission denied"


def _repo(wio: Wio) -> None:
    """Start the repository: `demo` beside `locked`, each with a rule.

    Args:
        wio: The facade.
    """
    wio.fixture(BASE)
    ruleset(wio, "demo", MANIFEST, {"ARC001": "keep"})
    ruleset(wio, "locked", MANIFEST, {"ARC001": "keep"})
    wio.put(f"{RULES}/locked/deep/ARC002-deep.md", rule("ARC002", "deep"))


_COMMANDS = {
    "config-check": ["config", "check"],
    "rules-check": ["rules", "check"],
    "rules-list": ["rules", "list"],
    "rules-show": ["rules", "show", "demo.ARC001"],
}
# `wio config check` reads the names of the ruleset directories and nothing below
# them, so it has no fault to name for a directory below a ruleset.
_CASES = [
    (command, where)
    for command in _COMMANDS
    for where in ("", "locked", "locked/deep")
    if not (command == "config-check" and where == "locked/deep")
]


@pytest.mark.parametrize(("command", "where"), _CASES)
def test_a_directory_that_cannot_be_listed_is_a_refusal_that_names_it(
    wio: Wio, sandbox: Sandbox, command: str, where: str
) -> None:
    """The command exits with an error at the directory and no traceback."""
    # Given a rules directory, a ruleset directory or one below it that is closed
    place = f"{RULES}/{where}".rstrip("/")
    _repo(wio)
    with unreadable(sandbox.root / RULES / where):
        # When the command runs
        output = wio.run(_COMMANDS[command])

    # Then it names the directory and says why, prints no traceback, and the
    # error is the only one about it: no ruleset is said to lack its manifest
    assert output.exit_code in (1, 2)
    assert f"{place}: {DENIED}" in output.stderr + output.stdout
    assert "Traceback" not in output.stderr
    assert "has no `ruleset.toml`" not in output.stderr + output.stdout
