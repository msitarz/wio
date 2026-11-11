# SPDX-License-Identifier: Apache-2.0
"""Scenarios of the `wio contracts` command group."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

HELP_LINE = "Create, list, check and show the Work contracts"


@pytest.mark.channels(Channel.CLI)
def test_contracts_prints_its_help_outside_a_repository(wio: Wio) -> None:
    """AC-1: `wio contracts` and `wio --help` work anywhere."""
    # Given a directory that is not in a git repository

    # When `wio contracts` and `wio --help` run there
    group = wio.run(["contracts"])
    listing = wio.run(["--help"])

    # Then the first prints a help text that names `wio contracts` and exits 0, and
    # the second lists `contracts` with its one-line help
    assert (group.exit_code, group.stderr) == (0, "")
    assert group.stdout.startswith("usage: wio contracts")
    assert listing.exit_code == 0
    assert "contracts" in listing.stdout
    assert HELP_LINE in listing.stdout


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_an_invalid_config_does_not_stop_the_help(wio: Wio) -> None:
    """AC-1: bare `wio contracts` reads no config."""
    # Given a repository whose config has an error
    wio.fixture("config/invalid")

    # When `wio contracts` runs there
    output = wio.run(["contracts"])

    # Then it prints its help and exits 0
    assert (output.exit_code, output.stderr) == (0, "")
    assert output.stdout.startswith("usage: wio contracts")
