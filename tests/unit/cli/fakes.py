# SPDX-License-Identifier: Apache-2.0
"""Fakes of the streams and of a component's command, for the tests of `wio.cli`."""

import io
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from tests.unit.fakes import FakeStdio
from wio import cli
from wio.cli.table import Entry

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace

    from wio.cli.ports import Command, CommandSpec
    from wio.io.ports import Stdio


@dataclass
class Spec:
    """A command spec with a name, a help text and an optional `--flag`."""

    name: str
    help: str
    flag: bool = False
    error: Exception | None = None

    def configure(self, parser: ArgumentParser) -> None:
        """Add `--flag` to the subparser when the spec has one.

        Args:
            parser: The subparser of the command.
        """
        if self.error:
            raise self.error
        if self.flag:
            parser.add_argument("--flag", action="store_true")


@dataclass
class Fake:
    """A command that counts how often it is described, wired and run."""

    spec: Spec
    code: int = 0
    described: int = 0
    wired: int = 0
    received: list[Namespace] = field(default_factory=list)
    fails_at: str = ""
    error: Exception | None = None

    @classmethod
    def failing(cls, step: str, error: Exception, name: str = "failing") -> Fake:
        """Make a fake that raises an error at one step of a run.

        Args:
            step: `describe`, `configure`, `wire` or `run`.
            error: What the step raises.
            name: The name of the subcommand.

        Returns:
            A fake named `name`, with the error at the step.
        """
        spec = Spec(name, "Fails.", error=error if step == "configure" else None)
        return cls(spec, fails_at=step, error=error)

    def _step(self, step: str) -> None:
        """Raise the error of this fake when it fails at the step.

        Args:
            step: The step that is being taken.
        """
        if self.error and self.fails_at == step:
            raise self.error

    def entry(self) -> Entry:
        """Make the table entry for this fake, under the package `config`.

        Returns:
            An entry whose functions count their calls.
        """
        return Entry(package="config", describe=self.describe, wire=self.wire)

    def describe(self) -> CommandSpec:
        """Count the call and return the spec.

        Returns:
            The spec of the fake.
        """
        self._step("describe")
        self.described += 1
        return self.spec

    def wire(self) -> Command:
        """Count the call and return the fake as the command.

        Returns:
            This fake.
        """
        self._step("wire")
        self.wired += 1
        return self

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Remember the arguments and answer with the fixed code.

        Args:
            args: The parsed arguments.
            stdio: Ignored.

        Returns:
            The exit code this fake was made with.
        """
        del stdio
        self._step("run")
        self.received.append(args)
        return self.code


def run_main(argv: list[str], table: list[Entry]) -> tuple[int, str, str]:
    """Run `main` on in-memory streams.

    Args:
        argv: The arguments after the program name.
        table: The entries of the subcommands.

    Returns:
        The exit code, standard output and standard error.
    """
    out, err = io.StringIO(), io.StringIO()
    code = cli.main(argv, FakeStdio(stdout=out, stderr=err), table)
    return code, out.getvalue(), err.getvalue()


def run_on_terminal(argv: list[str], table: list[Entry], stream: str) -> str:
    """Run `main` with one stream on a pseudo-terminal.

    Args:
        argv: The arguments after the program name.
        table: The entries of the subcommands.
        stream: `stdout` or `stderr`, the stream that is the terminal.

    Returns:
        What `main` wrote to the terminal.
    """
    master, slave = os.openpty()
    try:
        with os.fdopen(slave, "w") as terminal:
            stdio = (
                FakeStdio(stdout=terminal)
                if stream == "stdout"
                else FakeStdio(stderr=terminal)
            )
            cli.main(argv, stdio, table)
            terminal.flush()
            return os.read(master, 65536).decode()
    finally:
        os.close(master)
