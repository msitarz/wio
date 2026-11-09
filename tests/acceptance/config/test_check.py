# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio config check`, which prints the diagnostics of the config."""

from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

# Git runs in every scenario, so none of them is fast.
pytestmark = [
    pytest.mark.slow,
    pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI),
]


def test_a_valid_config_prints_nothing_and_an_invalid_one_fails(wio: Wio) -> None:
    """AC-1: errors print as `error: <key path>: <message>` and exit 1."""
    # Given a valid config, and a config with an unknown key
    # When `wio config check` runs on each
    # Then the first prints nothing and exits 0, the second prints the error, exits 1
    del wio
    pytest.skip("stub: the implementation stage writes this test")


def test_a_warning_is_printed_and_does_not_fail(wio: Wio) -> None:
    """AC-1: a warning of a check in `wio.config.CHECKS` exits 0."""
    # Given a valid config and a check put in CHECKS that returns a warning
    # When `wio config check` runs
    # Then it prints `warning: <where>: <message>` and exits 0
    del wio
    pytest.skip("stub: the implementation stage writes this test")


def test_json_prints_an_array_of_diagnostics(wio: Wio) -> None:
    """AC-1: `--json` prints `[]` or objects of severity, where and message."""
    # Given a valid config, and a config with an unknown key
    # When `wio config check --json` runs on each
    # Then the first prints `[]` and exits 0, the second one object and exits 1
    del wio
    pytest.skip("stub: the implementation stage writes this test")


def test_a_syntax_error_is_one_error_at_its_line_and_column(wio: Wio) -> None:
    """AC-1: the path is relative to the repository root."""
    # Given a config with a TOML syntax error
    # When `wio config check` runs
    # Then it prints one error at `.agents/wio/config.toml:<line>:<column>`, exit 1
    del wio
    pytest.skip("stub: the implementation stage writes this test")


@pytest.mark.channels(Channel.CLI)
def test_no_config_exits_2_with_a_message(wio: Wio) -> None:
    """AC-1: a directory outside any repository has no config to check."""
    # Given a directory outside any repository
    # When `wio config check` runs
    # Then it exits 2 with a message on standard error
    del wio
    pytest.skip("stub: the implementation stage writes this test")
