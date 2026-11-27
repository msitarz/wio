# SPDX-License-Identifier: Apache-2.0
"""Acceptance tests for `wio describe [<command>] [--json]`."""

import json
from typing import TYPE_CHECKING

import pytest

from tests.acceptance.channels import Channel

if TYPE_CHECKING:
    from tests.acceptance.dsl.wio import Wio


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_describe_prints_engine_overview_text_and_json(wio: Wio) -> None:
    """AC-1: `wio describe` prints deterministic text or JSON overview and exits 0."""
    # Given no repository or config is needed

    # When `wio describe` runs as text and as JSON
    text_run = wio.run(["describe"])
    json_run = wio.run(["describe", "--json"])

    # Then both exit 0 with deterministic, well-formed output
    assert text_run.exit_code == 0
    assert text_run.stdout.endswith("\n")
    assert not text_run.stdout.endswith("\n\n")
    assert "Exit codes:" in text_run.stdout
    assert "Commands:" in text_run.stdout

    assert json_run.exit_code == 0
    data = json.loads(json_run.stdout)
    assert [e["code"] for e in data["exit_codes"]] == [0, 1, 2, 70]
    assert "describe" in [c["name"] for c in data["commands"]]


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_describe_command_prints_semantics_and_reference_data(wio: Wio) -> None:
    """AC-2: `wio describe <command>` prints semantics and live tables and exits 0."""
    # Given no repository or config is needed

    # When `wio describe config` and `wio describe templates --json` run
    config_run = wio.run(["describe", "config"])
    templates_run = wio.run(["describe", "templates", "--json"])

    # Then both exit 0 with forms, invariants and code-derived reference data
    assert config_run.exit_code == 0
    assert config_run.stdout.endswith("\n")
    assert "Forms:" in config_run.stdout
    assert "Config schema keys:" in config_run.stdout

    assert templates_run.exit_code == 0
    data = json.loads(templates_run.stdout)
    assert data["name"] == "templates"
    assert data["references"][0]["title"] == "Template directives"


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_describe_unknown_command_exits_2_with_valid_choices(wio: Wio) -> None:
    """AC-3: `wio describe nosuch` (with or without `--json`) exits 2 with choices."""
    # Given an unknown command name

    # When `wio describe nosuch` runs with and without `--json`
    plain = wio.run(["describe", "nosuch"])
    as_json = wio.run(["describe", "nosuch", "--json"])

    # Then both exit 2 and name valid commands on stderr
    for result in (plain, as_json):
        assert result.exit_code == 2
        assert "nosuch" in result.stderr
        assert "config" in result.stderr
        assert "describe" in result.stderr


@pytest.mark.channels(Channel.IN_PROCESS, Channel.CLI)
def test_describe_works_outside_any_repository_without_config(wio: Wio) -> None:
    """AC-4: `wio describe` and `wio describe config` succeed outside a git repo."""
    # Given an empty directory with no .git and no .agents/wio/config.toml
    # (the default sandbox before any fixture or git init)

    # When `wio describe` and `wio describe config` run
    overview = wio.run(["describe"])
    config = wio.run(["describe", "config"])

    # Then both exit 0 without errors
    assert overview.exit_code == 0
    assert config.exit_code == 0
