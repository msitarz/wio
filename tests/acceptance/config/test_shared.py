# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio config` where it shares helpers with other commands."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_mistyped_setting_and_a_mistyped_key_name_the_closest(wio: Wio) -> None:
    """AC-4: the messages and exit codes of `show` and `check` are as before."""
    # Given a config with a `[stages]` table, and another whose stage `define` has
    # a `goal` and the key `sessionn`
    wio.fixture("config/rich")
    shown = wio.run(["config", "show", "stagez"])
    wio.fixture("config/shared-key-typo")

    # When `wio config show stagez` and `wio config check` run on them
    checked = wio.run(["config", "check"])

    # Then the first names `stagez` and `stages` and exits 2, and the second reports
    # `sessionn` and `session` and exits 1
    assert shown.exit_code == 2
    assert shown.stderr.startswith("error: no setting `stagez`. Did you mean `stages`?")
    assert checked.exit_code == 1
    assert checked.stdout.startswith(
        "error: stages.define.sessionn: unknown key `sessionn` in "
    )
    assert "Did you mean `session`?" in checked.stdout


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_a_warning_does_not_fail_the_check_and_an_error_does(wio: Wio) -> None:
    """AC-6: `wio config check` exits 0 for a warning alone and 1 for an error."""
    # Given a config with a warning and no error and one with an error
    quiet = wio.check_config("checks-quiet")
    loud = wio.check_config("checks-several")

    # When `wio config check` runs on both (above)

    # Then it exits 0 and then 1, with the output it had
    assert (quiet.exit_code, loud.exit_code) == (0, 1)
    assert quiet.stdout.startswith("warning: roots.docs.paths[0]:")
    assert "Config check passed" not in quiet.stdout
    assert loud.stdout.count("error: ") == 5
