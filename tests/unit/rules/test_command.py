# SPDX-License-Identifier: Apache-2.0
"""Tests of the group of subcommands of `wio rules`."""

import json
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tests.fakes import FakeEnvironment
from tests.unit.cli.fakes import run_main
from tests.unit.fakes import ROOT, FakeRepository, MemoryFileSystem
from wio.cli.table import COMMANDS, Entry
from wio.errors import DiagnosticsError, WioError
from wio.models.diagnostics import Diagnostic
from wio.rules import RulesCommand, Services, Subcommand, describe, json_option

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from wio.cli.ports import Command, CommandSpec
    from wio.io.ports import Stdio
    from wio.models.config import Config

type _Handler = Callable[[Services, Namespace, Stdio], int]


class _NoConfig:
    """Settings that a test of the group never loads."""

    def load(self) -> Config:
        """Refuse to load.

        Raises:
            AssertionError: Always, because the group must not read the config.
        """
        message = "the group loaded the config"
        raise AssertionError(message)


@dataclass
class _Probe:
    """What a table entry was wired with and run with."""

    wired: int = 0
    received: list[tuple[Services, Namespace]] = field(default_factory=list)


def _services() -> Services:
    """Build the services of a group over fakes.

    Returns:
        The services.
    """
    return Services(
        _NoConfig(), FakeRepository(), MemoryFileSystem(), FakeEnvironment(ROOT)
    )


def _entry(table: Sequence[Subcommand], probe: _Probe | None = None) -> Entry:
    """Make the table entry of the group over a table of subcommands.

    Args:
        table: The subcommands of the group.
        probe: Counts the wiring when given.

    Returns:
        An entry that describes and wires the real group over the table.
    """

    def wire() -> Command:
        """Build the group, counting the call.

        Returns:
            The command.
        """
        if probe is not None:
            probe.wired += 1
        return RulesCommand(_services(), table)

    def described() -> CommandSpec:
        """Describe the group over the table.

        Returns:
            The spec.
        """
        return describe(table)

    return Entry(package="rules", describe=described, wire=wire)


def _subcommand(
    name: str, handler: _Handler, configure: Callable[[ArgumentParser], None]
) -> Subcommand:
    """Make a subcommand with a help line.

    Args:
        name: Its name.
        handler: What it runs.
        configure: Adds its arguments.

    Returns:
        The subcommand.
    """
    return Subcommand(name, f"The {name}.", configure, handler)


def _flag(parser: ArgumentParser) -> None:
    """Add the argument `--flag`.

    Args:
        parser: The subparser.
    """
    parser.add_argument("--flag", action="store_true")


def _plain(_parser: ArgumentParser) -> None:
    """Add no argument."""


def _zero(_services: Services, _args: Namespace, _stdio: Stdio) -> int:
    """Succeed.

    Returns:
        0.
    """
    return 0


def test_the_component_is_listed_by_the_help_of_wio() -> None:
    """AC-1: `wio --help` lists `rules` with its description."""
    # Given the real table of commands

    # When `wio --help` runs
    code, out, _ = run_main(["--help"], list(COMMANDS))

    # Then it exits 0 and lists `rules` with its one line
    assert code == 0
    assert "rules" in out
    assert describe().help in out


def test_the_bare_command_prints_its_subcommands() -> None:
    """AC-1: `wio rules` prints the usage and each subcommand's help line."""
    # Given a table with the subcommands `alpha` and `beta`
    table = [
        _subcommand("alpha", _zero, _plain),
        _subcommand("beta", _zero, _plain),
    ]

    # When `wio rules` runs
    code, out, err = run_main(["rules"], [_entry(table)])

    # Then it prints the usage and both subcommands with their help, and exits 0
    assert (code, err) == (0, "")
    assert "usage: wio rules [-h] <subcommand> ..." in out
    assert "alpha" in out
    assert "The beta." in out


def test_a_subcommand_is_run_with_its_arguments_and_gives_the_exit_code() -> None:
    """AC-2: the handler gets the services, the namespace and the streams."""
    # Given a subcommand `alpha` with `--flag` that returns 1 when it is set
    probe = _Probe()

    def alpha(services: Services, args: Namespace, stdio: Stdio) -> int:
        probe.received.append((services, args))
        stdio.stdout.write("seen")
        return 1 if args.flag else 0

    entry = _entry([_subcommand("alpha", alpha, _flag)], probe)

    # When `wio rules alpha --flag` and `wio rules alpha` run
    flagged = run_main(["rules", "alpha", "--flag"], [entry])
    plain = run_main(["rules", "alpha"], [entry])

    # Then they exit 1 and 0, and the handler received the services and `flag`
    assert (flagged[0], plain[0]) == (1, 0)
    assert flagged[1] == "seen"
    assert [(type(s), a.flag) for s, a in probe.received] == [
        (Services, True),
        (Services, False),
    ]


def _fail_with(error: Exception) -> _Handler:
    """Make a handler that raises an error.

    Args:
        error: What it raises.

    Returns:
        The handler.
    """

    def handler(_services: Services, _args: Namespace, _stdio: Stdio) -> int:
        raise error

    return handler


def test_failures_map_to_exit_codes() -> None:
    """AC-3: a `WioError` and diagnostics exit 2, anything else exits 70."""
    # Given subcommands that raise a `WioError`, a `DiagnosticsError` and a bug
    diagnostics = [Diagnostic("error", "a", "one"), Diagnostic("error", "b", "two")]
    lines = "error: a: one\nerror: b: two"
    raised = {
        "mistake": WioError("cannot go on"),
        "findings": DiagnosticsError(lines, diagnostics),
        "bug": ValueError("broken"),
    }
    table = [_subcommand(n, _fail_with(e), _plain) for n, e in raised.items()]

    # When each runs
    found = {n: run_main(["rules", n], [_entry(table)]) for n in raised}

    # Then the messages go to standard error with exit 2, and the bug is 70
    assert found["mistake"] == (2, "", "error: cannot go on\n")
    assert found["findings"][0:2] == (2, "")
    assert found["findings"][2].splitlines() == lines.splitlines()
    assert found["bug"][0] == 70


def test_describing_is_light_and_only_the_chosen_subcommand_is_wired() -> None:
    """AC-4: the help does not wire the group, a subcommand does it once."""
    # Given an entry of `rules` whose wiring counts its calls
    probe = _Probe()
    entry = _entry([_subcommand("alpha", _zero, _plain)], probe)

    # When `wio --help` runs and then `wio rules alpha` runs
    run_main(["--help"], [entry])
    wired_by_help = probe.wired
    run_main(["rules", "alpha"], [entry])

    # Then the help did not wire the group and `alpha` wired it once
    assert (wired_by_help, probe.wired) == (0, 1)


def test_json_has_one_declaration_and_one_behaviour() -> None:
    """AC-5: one document on exit 0 and 1, and nothing on stdout for exit 2."""

    # Given a subcommand that declares `--json` with the helper and writes one
    # object, returning the code that it is told to
    def configure(parser: ArgumentParser) -> None:
        json_option(parser, help="Write JSON.")
        parser.add_argument("--code", type=int, default=0)

    def alpha(_services: Services, args: Namespace, stdio: Stdio) -> int:
        if args.code == 2:
            message = "cannot go on"
            raise WioError(message)
        stdio.stdout.write(json.dumps({"ok": args.code == 0}))
        return int(args.code)

    entry = _entry([_subcommand("alpha", alpha, configure)])

    # When it runs with `--json` and returns 0, 1 and raises a `WioError`
    found = [
        run_main(["rules", "alpha", "--json", "--code", str(c)], [entry])
        for c in (0, 1, 2)
    ]

    # Then the first two hold one JSON document, and the third holds nothing
    assert [json.loads(out) for _, out, _ in found[:2]] == [{"ok": True}, {"ok": False}]
    assert (found[2][1], found[2][2]) == ("", "error: cannot go on\n")
