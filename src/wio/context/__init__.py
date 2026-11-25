# SPDX-License-Identifier: Apache-2.0
"""The `wio context` command: compiling what an agent session reads for a stage.

A run loads only the modules that it needs. In particular it loads neither
`tomlkit` nor the command modules of the other components:
`wio.config.command`, `wio.contracts.command`, `wio.log.command`,
`wio.rules.command`, `wio.templates.command` and `wio.trailers.command`.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.models.bundle import CompiledBundle
lazy from wio.context.command import ContextCommand
lazy from wio.context.compiler import Compiler

if TYPE_CHECKING:
    from argparse import ArgumentParser
    from collections.abc import Callable, Sequence

    from wio.env.ports import Environment
    from wio.io.ports import FileSystem, Repository

type Check = Callable[[str, str, str], Sequence[str]]
"""A check of the inputs, run before the bundle is composed.

It takes the Work's id, the action and the stage, and returns the text of its
warnings, each one line without the `warning: ` prefix, or raises a `WioError`
for an input that gets no bundle.
"""


@dataclass(frozen=True)
class Services:
    """What `wio context` reads the project and writes its results through.

    Provisional: a Work that needs another port adds a field.

    Attributes:
        repository: Finds the repository.
        files: Reads and writes files.
        environment: Gives the environment variables and the working directory.
    """

    repository: Repository
    files: FileSystem
    environment: Environment


@dataclass(frozen=True)
class Compiled:
    """What the compiler hands to the command.

    Attributes:
        bundle: The composed bundle.
        warnings: The warnings of the checks, in the order the checks ran.
    """

    bundle: CompiledBundle
    warnings: tuple[str, ...]


class ContextSpec:
    """What the usage needs to know about `wio context`, and nothing more."""

    name = "context"
    help = "Print what an agent session reads for a stage of a Work."

    def configure(self, parser: ArgumentParser) -> None:
        """Add the Work, the action and the stage, in that order.

        It does no I/O and loads no module of the package. The parsed arguments
        carry them as `work`, `action` and `stage`. There is no `--json`: the
        command prints raw text for a session to read.

        Args:
            parser: The subparser that `wio.cli` created for `context`.
        """
        parser.add_argument("work", metavar="<work>", help="The id of the Work.")
        parser.add_argument("action", metavar="<action>", help="The action.")
        parser.add_argument("stage", metavar="<stage>", help="The stage.")


def describe() -> ContextSpec:
    """Describe `wio context` without loading its implementation.

    Returns:
        The command spec of `context`.
    """
    return ContextSpec()


__all__ = [
    "Check",
    "Compiled",
    "CompiledBundle",
    "Compiler",
    "ContextCommand",
    "ContextSpec",
    "Services",
    "describe",
]
