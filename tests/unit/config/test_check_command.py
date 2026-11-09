# SPDX-License-Identifier: Apache-2.0
"""Tests of `wio config check` run through the command line with fake ports."""

import pytest


def test_check_runs_the_checks_that_are_put_in_checks() -> None:
    """AC-1: the command reads `wio.config.CHECKS` when it runs."""
    # Given a valid config and a check appended to `wio.config.CHECKS`
    # When `wio config check` runs
    # Then the check's diagnostic is printed
    pytest.skip("stub: the implementation stage writes this test")


def test_check_refuses_when_there_is_no_config_to_check() -> None:
    """AC-1: no repository, no file and an unreadable file are refused."""
    # Given no repository, no config file and an unreadable config file
    # When `wio config check` runs on each
    # Then each raises `ConfigurationError` and nothing reaches standard output
    pytest.skip("stub: the implementation stage writes this test")


def test_check_is_a_view_of_config_with_a_json_flag() -> None:
    """AC-1: `wio config check [--json]` is parsed."""
    # Given the usage of `wio config`
    # When `check` and `check --json` are parsed
    # Then `config_view` is `check` and `json` is false and true
    pytest.skip("stub: the implementation stage writes this test")
