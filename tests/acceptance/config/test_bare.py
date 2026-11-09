# SPDX-License-Identifier: Apache-2.0
"""Scenarios of bare `wio config`, which shows what the component offers."""

from typing import TYPE_CHECKING

from tests.acceptance.channels import IN_BOTH

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


@IN_BOTH
def test_bare_config_shows_the_help(wio: Wio) -> None:
    """AC-1: bare `wio config` names its subcommands and exits 0."""
    # Given a repository with a valid config
    wio.fixture("config/rich")

    # When `wio config` runs
    output = wio.run(["config"])

    # Then the output names list and show and the exit code is 0
    assert "list" in output.stdout
    assert "show" in output.stdout
    assert output.exit_code == 0
