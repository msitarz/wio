# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio templates` where it shares helpers with other commands."""

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio
    from tests.sandbox import Sandbox

REPOSITORY = Path(__file__).resolve().parents[3]
DIR = ".agents/wio/templates"


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_mistyped_key_in_a_template_names_the_closest(wio: Wio) -> None:
    """AC-5: `descriptions` gets a suggestion and `zzz` does not."""
    # Given a config with the kind `feature` and two templates, one with the key
    # `descriptions` and one with the key `zzz`
    wio.fixture("templates/shared-keys")

    # When `wio templates check` runs
    output = wio.run(["templates", "check"])

    # Then it reports both unknown keys, the first with
    # `Did you mean `description`?`, each at its file, and exits 1
    expected = (
        f"error: {DIR}/close.md: Unknown key `descriptions` in the metadata. "
        "Did you mean `description`?\n"
        f"error: {DIR}/far.md: Unknown key `zzz` in the metadata\n"
    )
    assert (output.stdout, output.exit_code) == (expected, 1)


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_the_templates_commands_print_what_they_printed(
    wio: Wio, sandbox: Sandbox
) -> None:
    """AC-9: the repository's templates and a templates directory that is a link."""
    # Given this repository's templates, and a repository whose templates
    # directory is a symbolic link
    wio.fixture("templates/none")
    shutil.copytree(
        REPOSITORY / ".agents", sandbox.root / ".agents", dirs_exist_ok=True
    )
    commands = (["list"], ["check"], ["check", "--json"])

    # When `list`, `check` and `check --json` run on each
    whole = [wio.run(["templates", *command]) for command in commands]
    shutil.rmtree(sandbox.root / DIR)
    (sandbox.root / DIR).symlink_to(sandbox.root / ".agents" / "wio" / "rules")
    linked = [wio.run(["templates", *command]) for command in commands]

    # Then the first prints what it printed and `The templates pass.`, and the
    # second reports the link with exit 1 for `check` and 2 for `list`
    assert [(o.exit_code, o.stdout) for o in whole[1:]] == [
        (0, "The templates pass.\n"),
        (0, "[]\n"),
    ]
    assert whole[0].exit_code == 0
    assert all(name in whole[0].stdout for name in ("feature.draft", "feature.leaf"))
    message = f"error: {DIR}: The templates directory must not be a symbolic link\n"
    assert (linked[1].stdout, linked[1].exit_code) == (message, 1)
    assert linked[2].exit_code == 1
    assert (linked[0].exit_code, linked[0].stdout) == (2, "")
    assert linked[0].stderr == f"{message}`wio templates check` shows every problem.\n"
