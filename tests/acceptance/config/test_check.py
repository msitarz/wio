# SPDX-License-Identifier: Apache-2.0
"""Scenarios of `wio config check`, which prints the diagnostics of the config."""

import json
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio

# The CLI channel runs only under `make slow`; the in-process run stays fast.
pytestmark = pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)


def test_a_valid_config_prints_nothing_and_an_invalid_one_fails(wio: Wio) -> None:
    """AC-1: errors print as `error: <key path>: <message>` and exit 1."""
    # Given a valid config, and a config with an unknown key
    # When `wio config check` runs on each
    wio.fixture("config/rich")
    valid = wio.run(["config", "check"])
    wio.fixture("config/invalid")
    invalid = wio.run(["config", "check"])

    # Then the first says it passed and exits 0, the second prints the error, exits 1
    assert (valid.stdout, valid.exit_code) == ("Config check passed!\n", 0)
    assert invalid.stdout.startswith("error: works.nonsense: unknown key `nonsense`")
    assert invalid.exit_code == 1


def test_json_prints_an_array_of_diagnostics(wio: Wio) -> None:
    """AC-1: `--json` prints `[]` or objects of severity, where and message."""
    # Given a valid config, and a config with an unknown key
    # When `wio config check --json` runs on each
    wio.fixture("config/rich")
    valid = wio.run(["config", "check", "--json"])
    wio.fixture("config/invalid")
    invalid = wio.run(["config", "check", "--json"])

    # Then the first prints `[]` and exits 0, the second one object and exits 1
    assert (json.loads(valid.stdout), valid.exit_code) == ([], 0)
    found = json.loads(invalid.stdout)
    assert len(found) == 1
    assert set(found[0]) == {"severity", "where", "message"}
    assert (found[0]["severity"], invalid.exit_code) == ("error", 1)


def test_a_syntax_error_is_one_error_at_its_line_and_column(wio: Wio) -> None:
    """AC-1: the path is relative to the repository root."""
    # Given a config with a TOML syntax error
    wio.fixture("config/syntax-error")

    # When `wio config check` runs
    output = wio.run(["config", "check"])

    # Then it prints one error at `.agents/wio/config.toml:<line>:<column>`, exit 1
    lines = output.stdout.splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("error: .agents/wio/config.toml:3:7: ")
    assert output.exit_code == 1


@pytest.mark.channels(Channel.CLI)
def test_no_config_exits_2_with_a_message(wio: Wio) -> None:
    """AC-1: a directory outside any repository has no config to check."""
    # Given a directory outside any repository

    # When `wio config check` runs
    output = wio.run(["config", "check"])

    # Then it exits 2 with a message on standard error
    assert output.exit_code == 2
    assert output.stdout == ""
    assert "run wio from a directory inside the repository" in output.stderr
