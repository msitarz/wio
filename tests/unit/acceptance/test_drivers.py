# SPDX-License-Identifier: Apache-2.0
"""Tests for the facade and the test drivers of the acceptance setup."""

import subprocess
from typing import TYPE_CHECKING, Any

from tests.acceptance.drivers.base import RunResult
from tests.acceptance.drivers.cli import SCRIPT, CliDriver
from tests.acceptance.drivers.in_process import InProcessDriver
from tests.acceptance.dsl.results import Output
from tests.acceptance.dsl.wio import Wio

if TYPE_CHECKING:
    from collections.abc import Sequence

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

    def install(self, fixture: str) -> None:
        """Install nothing.

        Args:
            fixture: Ignored.
        """
        del fixture


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
        self.installed: list[str] = []

    def run(self, args: Sequence[str]) -> RunResult:
        """Record the arguments.

        Args:
            args: The arguments after the program name.

        Returns:
            A silent success.
        """
        self.arguments.append(args)
        return RunResult("", "", 0)

    def install(self, fixture: str) -> None:
        """Record the fixture.

        Args:
            fixture: The fixture the facade asked for.
        """
        self.installed.append(fixture)


def test_the_facade_runs_any_command_with_its_arguments() -> None:
    """`run` hands the arguments to the driver as they are given."""
    # Given a facade over a recording driver
    driver = RecordingDriver()
    wio = Wio(driver)

    # When a command runs through the facade
    output = wio.run(["config", "show", "works", "--json"])

    # Then the driver ran those arguments and the output is the driver's result
    assert driver.arguments == [["config", "show", "works", "--json"]]
    assert output == Output(stdout="", stderr="", exit_code=0)


def test_the_facade_installs_a_fixture_by_name() -> None:
    """`fixture` asks the driver for the sample repository of that name."""
    # Given a facade over a recording driver
    driver = RecordingDriver()
    wio = Wio(driver)

    # When a scenario starts from a fixture
    wio.fixture("config/rich")

    # Then the driver was asked to install it
    assert driver.installed == ["config/rich"]


def test_a_driver_copies_the_fixture_into_its_sandbox(sandbox: Sandbox) -> None:
    """The files of the fixture are in the sandbox, nested directories included."""
    # Given the in-process driver, whose install starts no process
    driver = InProcessDriver(sandbox)

    # When it installs the rich config fixture
    driver.install("config/rich")

    # Then the config file is at its place in the sandbox's root
    config = sandbox.root / ".agents" / "wio" / "config.toml"
    assert "[works]" in config.read_text(encoding="utf-8")


def test_the_cli_driver_makes_the_installed_fixture_a_git_repository(
    sandbox: Sandbox, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The CLI channel runs `git init` after copying, as a user has a repository."""
    # Given the CLI driver and a spy in place of starting git
    calls = _spy_on_subprocess(monkeypatch)

    # When it installs a fixture
    CliDriver(sandbox).install("config/rich")

    # Then git was initialized in the sandbox and the files are there
    assert calls[0]["command"] == ["git", "init", "--quiet"]
    assert calls[0]["cwd"] == sandbox.root
    assert (sandbox.root / ".agents" / "wio" / "config.toml").is_file()
