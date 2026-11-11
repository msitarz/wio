# SPDX-License-Identifier: Apache-2.0
"""Tests of the group of subcommands of `wio contracts`."""

import pytest


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_subcommand_in_the_table_is_described_and_run() -> None:
    """AC-2: the help lists `ping`, and `ping` prints `pong`."""
    # Given a group built with a table of one entry `ping`, whose handler writes `pong`
    # When `wio contracts --help` and `wio contracts ping` run through it
    # Then the help lists `ping` and the second prints `pong` and exits 0


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_an_unknown_subcommand_is_a_usage_error() -> None:
    """AC-2: `nosuch` is named and the exit code is 2."""
    # Given the same group
    # When `wio contracts nosuch` runs
    # Then it prints a usage error that names `nosuch` and exits 2


@pytest.mark.skip(reason="Pending the implementation stage.")
def test_a_contracts_error_exits_2_and_a_failed_check_exits_1() -> None:
    """AC-6: the message goes to standard error for 2, and nothing for 1."""
    # Given a group with a subcommand that raises `ContractsError("no such Work")`
    # and one that returns 1
    # When each runs
    # Then the first writes the message to standard error and exits 2, and the second
    # exits 1 with nothing on standard error
