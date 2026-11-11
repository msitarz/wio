# SPDX-License-Identifier: Apache-2.0
"""The table of the subcommands of `wio contracts`: one entry for each."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from argparse import ArgumentParser, Namespace
    from collections.abc import Callable, Sequence

    from wio.contracts.ports import TemplateCatalog
    from wio.io.ports import FileSystem, Repository, Stdio
    from wio.ports import Settings


@dataclass(frozen=True)
class Services:
    """What a subcommand reads the project through.

    Provisional: a leaf that needs another port, such as randomness, adds a field.

    Attributes:
        settings: Loads the config.
        repository: Finds the repository root.
        files: Lists and reads files.
        catalog: Finds the templates of the project.
    """

    settings: Settings
    repository: Repository
    files: FileSystem
    catalog: TemplateCatalog


@dataclass(frozen=True)
class Subcommand:
    """One subcommand of `wio contracts`, described and run apart.

    Provisional: the field names and the handler's signature may change, and the
    entry holds at least these four things.

    Attributes:
        name: The subcommand's name, as typed after `wio contracts`.
        help: One line that `wio contracts --help` shows for it.
        configure: Adds its arguments to its subparser. It does no I/O, because
            it runs on every run.
        handler: Runs it with the services, the parsed arguments and the
            streams, and returns the exit code: 0, or 1 for a failed check. A
            mistake the user must fix is a `ContractsError`, and not a code.
    """

    name: str
    help: str
    configure: Callable[[ArgumentParser], None]
    handler: Callable[[Services, Namespace, Stdio], int]


SUBCOMMANDS: Final[Sequence[Subcommand]] = ()
"""The subcommands of `wio contracts`, to which each leaf adds its own entry."""
