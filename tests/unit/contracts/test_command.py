# SPDX-License-Identifier: Apache-2.0
"""Tests of the group of subcommands of `wio contracts`."""

from typing import TYPE_CHECKING

from tests.unit.cli.fakes import run_main
from tests.unit.fakes import FakeRepository, MemoryFileSystem
from wio.cli.table import Entry
from wio.contracts import (
    ContractsCommand,
    ContractsError,
    Services,
    Subcommand,
    describe,
)

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from collections.abc import Callable, Sequence

    from wio.cli.ports import Command, CommandSpec
    from wio.io.ports import Stdio
    from wio.models.config import Config
    from wio.models.template import Template


class _Settings:
    """A `Settings` that fails: the group must not load the config."""

    def load(self) -> Config:
        """Fail.

        Raises:
            AssertionError: Always.
        """
        message = "the group loaded the config"
        raise AssertionError(message)


class _Catalog:
    """A catalog that holds no template."""

    def find(self, name: str) -> Template | None:  # noqa: ARG002
        """Find nothing.

        Args:
            name: The name asked for.

        Returns:
            None.
        """
        return None

    def is_rejected(self, name: str) -> bool:  # noqa: ARG002
        """Reject nothing.

        Args:
            name: The name asked for.

        Returns:
            False.
        """
        return False


def _nothing(_parser: ArgumentParser) -> None:
    """Add no argument to a subparser."""


def _entry(table: Sequence[Subcommand]) -> Entry:
    """Make the table entry of a `contracts` group over a table of subcommands.

    Args:
        table: The subcommands of the group.

    Returns:
        An entry that describes and wires the real group over the table.
    """

    def wire() -> Command:
        """Build the group over fakes of the services.

        Returns:
            The command.
        """
        services = Services(
            _Settings(), FakeRepository(), MemoryFileSystem(), _Catalog()
        )
        return ContractsCommand(services, table)

    def described() -> CommandSpec:
        """Describe the group over the table.

        Returns:
            The spec.
        """
        return describe(table)

    return Entry(package="contracts", describe=described, wire=wire)


def _pong(_services: Services, _args: Namespace, stdio: Stdio) -> int:
    """Write `pong`.

    Args:
        _services: Unused.
        _args: Unused.
        stdio: Where to write.

    Returns:
        0.
    """
    stdio.stdout.write("pong\n")
    return 0


def _raises(_services: Services, _args: Namespace, _stdio: Stdio) -> int:
    """Fail as a subcommand does for what the user must fix.

    Raises:
        ContractsError: Always.
    """
    message = "no such Work"
    raise ContractsError(message)


def _failed_check(_services: Services, _args: Namespace, _stdio: Stdio) -> int:
    """Answer as a check that failed.

    Returns:
        1.
    """
    return 1


def _table(name: str, handler: Callable[[Services, Namespace, Stdio], int]) -> Entry:
    """Make an entry of a group with one subcommand.

    Args:
        name: The subcommand's name.
        handler: What it runs.

    Returns:
        The entry for the table of commands.
    """
    return _entry([Subcommand(name, f"The {name}.", _nothing, handler)])


def test_a_subcommand_in_the_table_is_described_and_run() -> None:
    """AC-2: the help lists `ping`, and `ping` prints `pong`."""
    # Given a group built with a table of one entry `ping`, whose handler writes
    # `pong`
    entry = _table("ping", _pong)

    # When `wio contracts --help` and `wio contracts ping` run through it
    helped = run_main(["contracts", "--help"], [entry])
    ran = run_main(["contracts", "ping"], [entry])

    # Then the help lists `ping` and the second prints `pong` and exits 0
    assert helped[0] == 0
    assert "ping" in helped[1]
    assert ran == (0, "pong\n", "")


def test_an_unknown_subcommand_is_a_usage_error() -> None:
    """AC-2: `nosuch` is named and the exit code is 2."""
    # Given the same group
    entry = _table("ping", _pong)

    # When `wio contracts nosuch` runs
    code, out, err = run_main(["contracts", "nosuch"], [entry])

    # Then it prints a usage error that names `nosuch` and exits 2
    assert (code, out) == (2, "")
    assert "nosuch" in err


def test_a_contracts_error_exits_2_and_a_failed_check_exits_1() -> None:
    """AC-6: the message goes to standard error for 2, and nothing for 1."""
    # Given a group with a subcommand that raises `ContractsError("no such Work")`
    # and one that returns 1
    mistake = _table("mistake", _raises)
    check = _table("check", _failed_check)

    # When each runs
    first = run_main(["contracts", "mistake"], [mistake])
    second = run_main(["contracts", "check"], [check])

    # Then the first writes the message to standard error and exits 2, and the
    # second exits 1 with nothing on standard error
    assert first == (2, "", "error: no such Work\n")
    assert second == (1, "", "")
