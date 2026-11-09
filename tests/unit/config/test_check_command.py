# SPDX-License-Identifier: Apache-2.0
"""Tests of `wio config check` run through the command line with fake ports."""

import contextlib
import io
from dataclasses import dataclass
from typing import TextIO

import pytest

from tests.unit.config.fakes import CONFIG, FakeRepository, MemoryFileSystem
from wio import cli
from wio.cli.table import component_entry
from wio.config import ConfigCommand


@dataclass
class _Stdio:
    """In-memory standard streams that satisfy the `Stdio` port."""

    stdin: TextIO
    stdout: TextIO
    stderr: TextIO


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
    """AC-1: `wio config check [--json]` is described by the usage."""
    # Given a repository with a valid config
    files = MemoryFileSystem({CONFIG: ""})
    entry = component_entry("config", lambda: ConfigCommand(FakeRepository(), files))

    # When the usage of `wio config` and of `wio config check` is asked for
    bare, usage = io.StringIO(), io.StringIO()
    cli.main(["config"], _Stdio(io.StringIO(), bare, io.StringIO()), (entry,))
    with contextlib.suppress(SystemExit):
        cli.main(
            ["config", "check", "--help"],
            _Stdio(io.StringIO(), usage, io.StringIO()),
            (entry,),
        )

    # Then the first names `check`, and the second the flag
    assert "check" in bare.getvalue()
    assert "usage: wio config check [-h] [--json]" in usage.getvalue()
