# SPDX-License-Identifier: Apache-2.0
"""Tests of `wio config check` run through the command line with fake ports."""

import contextlib
import io
from dataclasses import dataclass
from typing import TYPE_CHECKING, TextIO

import pytest

import wio.config
from tests.unit.config.fakes import CONFIG, FakeRepository, MemoryFileSystem
from wio import cli
from wio.cli.table import component_entry
from wio.config import CheckInputs, ConfigCommand
from wio.models.diagnostics import Diagnostic

if TYPE_CHECKING:
    from wio.models.config import Config


@dataclass
class _Stdio:
    """In-memory standard streams that satisfy the `Stdio` port."""

    stdin: TextIO
    stdout: TextIO
    stderr: TextIO


def _run(
    files: MemoryFileSystem, repository: FakeRepository, *argv: str
) -> tuple[int, str]:
    """Run `wio config check ...` on fake ports, writing to a captured stdout.

    Args:
        files: The files the loader reads.
        repository: The repository the loader finds.
        *argv: The arguments after `wio config check`.

    Returns:
        The exit code and what was written to standard output.
    """
    entry = component_entry("config", lambda: ConfigCommand(repository, files))
    out = io.StringIO()
    stdio = _Stdio(io.StringIO(), out, io.StringIO())
    code = cli.main(["config", "check", *argv], stdio, (entry,))
    return code, out.getvalue()


def test_check_runs_the_checks_that_are_put_in_checks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-1: the command reads `wio.config.CHECKS` when it runs."""

    # Given a valid config and a check appended to `wio.config.CHECKS`
    def warn(config: Config, inputs: CheckInputs) -> list[Diagnostic]:
        del config, inputs
        return [Diagnostic("warning", "works", "a warning")]

    monkeypatch.setattr(wio.config, "CHECKS", (warn,))
    files = MemoryFileSystem({CONFIG: ""})

    # When `wio config check` runs
    code, out = _run(files, FakeRepository())

    # Then the check's diagnostic is printed and the run succeeds
    assert out == "warning: works: a warning\n"
    assert code == 0


@pytest.mark.parametrize(
    ("files", "repository"),
    [
        (MemoryFileSystem({CONFIG: ""}), FakeRepository(top=None)),
        (MemoryFileSystem(), FakeRepository()),
        (MemoryFileSystem({CONFIG: ""}, failure=PermissionError()), FakeRepository()),
    ],
    ids=["no repository", "no file", "unreadable file"],
)
def test_check_refuses_when_there_is_no_config_to_check(
    files: MemoryFileSystem, repository: FakeRepository
) -> None:
    """AC-1: no repository, no file and an unreadable file are refused."""
    # Given no repository, no config file or an unreadable config file

    # When `wio config check` runs
    code, out = _run(files, repository)

    # Then the command line exits 2 and nothing reaches standard output
    assert code == 2
    assert out == ""


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
