# SPDX-License-Identifier: Apache-2.0
"""Run the selected log command over the adapters supplied by the CLI.

Bare help can run in any working directory.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argparse import Namespace

    from wio.env.ports import Directories
    from wio.io.ports import FileSystem, Repository, Stdio


@dataclass(frozen=True)
class LogCommand:
    """The log command wired to the ports shared by its forms.

    Attributes:
        repository: Supplies the identity of the clone.
        directories: Supplies the Wio home.
        filesystem: Reads the clone's log files.
    """

    repository: Repository
    directories: Directories
    filesystem: FileSystem

    def run(self, args: Namespace, stdio: Stdio) -> int:
        """Run the chosen form of the command.

        Args:
            args: The parsed help or show arguments.
            stdio: Receives the report and any text-form note.

        Returns:
            Zero for help or a readable log, including an empty log.

        Raises:
            WioError: The log cannot be located or read.
        """
        raise NotImplementedError
