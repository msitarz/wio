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
lazy from wio.context.composition import Composition
lazy from wio.context.heading import header
lazy from wio.context.identity import bundle_id

if TYPE_CHECKING:
    from argparse import ArgumentParser
    from collections.abc import Callable, Sequence

    from wio.context.ports import ReviewedCommit
    from wio.env.ports import Directories, Environment
    from wio.io.ports import FileSystem, Repository
    from wio.ports import EventSink, Settings

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
        directories: Finds the temporary directory for default file delivery.
        settings: Gives the configured bundle size threshold.
        events: Records the stage-entry event after delivery.
        reviewed: Finds the starting commit for a gate stage.
    """

    repository: Repository
    files: FileSystem
    environment: Environment
    directories: Directories
    settings: Settings
    events: EventSink
    reviewed: ReviewedCommit


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
        """Add the Work, action, stage and optional file delivery.

        It does no I/O and loads no module of the package. The parsed arguments
        carry them as `work`, `action`, `stage` and `output`. There is no
        `--json`: the command delivers raw text for a session to read.

        Args:
            parser: The subparser that `wio.cli` created for `context`.
        """
        parser.add_argument("work", metavar="<work>", help="The id of the Work.")
        parser.add_argument("action", metavar="<action>", help="The action.")
        parser.add_argument("stage", metavar="<stage>", help="The stage.")
        parser.add_argument(
            "--output",
            nargs="?",
            const=None,
            default=False,
            type=_output_path,
            metavar="<path>",
            help="Write the bundle to a file and print its path.",
        )


def _output_path(value: str) -> str:
    """Accept a non-empty file path for the output option.

    Args:
        value: The path as supplied on the command line.

    Returns:
        The path unchanged.

    Raises:
        ArgumentTypeError: If the path is empty.
    """
    if not value:
        from argparse import ArgumentTypeError

        message = "output path cannot be empty"
        raise ArgumentTypeError(message)
    return value


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
    "Composition",
    "ContextCommand",
    "ContextSpec",
    "Services",
    "bundle_id",
    "describe",
    "header",
]
