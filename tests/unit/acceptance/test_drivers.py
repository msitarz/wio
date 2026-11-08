# SPDX-License-Identifier: Apache-2.0
"""Tests for the facade and the test drivers of the acceptance setup."""

import subprocess
from typing import TYPE_CHECKING, Any

from tests.acceptance.drivers.base import RunResult
from tests.acceptance.drivers.cli import SCRIPT, CliDriver
from tests.acceptance.dsl.results import Output
from tests.acceptance.dsl.wio import Wio

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    import pytest

    from tests.sandbox import Sandbox


class FakeDriver:
    """A test driver that returns a fixed result."""

    def run(self, args: Sequence[str]) -> RunResult:
        """Answer with a fixed result whatever the arguments.

        Args:
            args: The arguments, ignored.

        Returns:
            The fixed result.
        """
        del args
        return RunResult("usage\n", "warning\n", 3)

    def prepare(self, files: Mapping[str, str]) -> None:
        """Prepare nothing.

        Args:
            files: Ignored.
        """
        del files


def _spy_on_subprocess(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Replace `subprocess.run` with a spy that records each call.

    Args:
        monkeypatch: The test's monkeypatch fixture.

    Returns:
        The list the spy appends each call to.
    """
    calls: list[dict[str, Any]] = []

    def spy(
        command: list[str],
        **kwargs: Any,  # noqa: ANN401
    ) -> subprocess.CompletedProcess[str]:
        """Record the call and answer with a silent success.

        Args:
            command: The command line.
            **kwargs: The options of the call.

        Returns:
            A completed process with no output.
        """
        calls.append({"command": command, **kwargs})
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", spy)
    return calls


def test_the_facade_maps_a_result_to_an_output() -> None:
    """`bare()` turns the driver's result into both streams and an exit code."""
    # Given a fake test driver that returns a result
    wio = Wio(FakeDriver())

    # When wio is run bare through the facade
    output = wio.bare()

    # Then the output carries both streams and the exit code
    assert output == Output(stdout="usage\n", stderr="warning\n", exit_code=3)


def test_the_cli_driver_runs_in_the_sandbox(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The subprocess gets the sandbox's directory and environment."""
    # Given the CLI driver and a spy in place of starting a process
    calls = _spy_on_subprocess(monkeypatch)

    # When it runs wio
    CliDriver(sandbox).run(["x"])

    # Then the spy received the command, the sandbox's root and its environment
    assert calls[0]["command"] == [str(SCRIPT), "x"]
    assert calls[0]["cwd"] == sandbox.root
    assert calls[0]["env"] == sandbox.env


class RecordingDriver:
    """A test driver that records what the facade asks of it."""

    def __init__(self) -> None:
        """Start with nothing recorded."""
        self.arguments: list[Sequence[str]] = []
        self.prepared: list[Mapping[str, str]] = []

    def run(self, args: Sequence[str]) -> RunResult:
        """Record the arguments.

        Args:
            args: The arguments after the program name.

        Returns:
            A silent success.
        """
        self.arguments.append(args)
        return RunResult("", "", 0)

    def prepare(self, files: Mapping[str, str]) -> None:
        """Record the files.

        Args:
            files: The files the facade asked for.
        """
        self.prepared.append(files)


def test_the_facade_runs_config_with_its_arguments() -> None:
    """`run_config` puts `config` before the arguments."""
    # Given a facade over a recording driver
    driver = RecordingDriver()
    wio = Wio(driver)

    # When wio config runs through the facade
    output = wio.run_config("show", "works", "--json")

    # Then the driver ran `config show works --json` and the output is silent
    assert driver.arguments == [["config", "show", "works", "--json"]]
    assert output == Output(stdout="", stderr="", exit_code=0)


def test_the_facade_prepares_the_config_file() -> None:
    """`with_config` asks for the config file at its place."""
    # Given a facade over a recording driver
    driver = RecordingDriver()
    wio = Wio(driver)

    # When a config is given to the facade
    wio.with_config("[works]\n")

    # Then the driver was asked for that file in `.agents/wio`
    assert driver.prepared == [{".agents/wio/config.toml": "[works]\n"}]


def test_the_driver_prepares_a_git_repository_with_the_files(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The sandbox gets `git init` and each file, with its directories."""
    # Given the CLI driver and a spy in place of starting git
    calls = _spy_on_subprocess(monkeypatch)

    # When it prepares a file in a directory
    CliDriver(sandbox).prepare({"a/b.txt": "text"})

    # Then git was initialized in the sandbox and the file was written
    assert calls[0]["command"] == ["git", "init", "--quiet"]
    assert calls[0]["cwd"] == sandbox.root
    assert (sandbox.root / "a" / "b.txt").read_text(encoding="utf-8") == "text"
