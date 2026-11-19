# SPDX-License-Identifier: Apache-2.0
"""Stamp events and append them to the log shared by a clone's worktrees.

The sink contains failures at the recording boundary so callers can keep
their result when the log is unavailable.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.env.ports import Clock, Directories, Environment
    from wio.io.ports import FileSystem, Repository, Stdio
    from wio.models.config import Log
    from wio.models.events import Event


@dataclass(frozen=True)
class LogSink:
    """Append events through the ports of the current command.

    Attributes:
        environment: Source of the working directory, switch and session variables.
        clock: Source of the envelope timestamp.
        directories: Source of the Wio home.
        repository: Source of the clone identity.
        filesystem: Appends the encoded line to the clone's events file.
        stdio: Standard error receives identification and recording warnings.
        log: Effective harness mappings, preferences and extra recorded variables.
    """

    environment: Environment
    clock: Clock
    directories: Directories
    repository: Repository
    filesystem: FileSystem
    stdio: Stdio
    log: Log

    def write(self, event: Event) -> None:
        """Stamp one event and append it to the clone's events file.

        The exact switch value `off` short-circuits recording before location.
        Location and write failures are reported to standard error when possible.
        Only append permission failures using the default Wio home get a hint.

        Args:
            event: The review or context event to stamp and append.
        """
        raise NotImplementedError
