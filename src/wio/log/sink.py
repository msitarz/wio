# SPDX-License-Identifier: Apache-2.0
"""Stamp events and append them to the log shared by a clone's worktrees.

The sink contains failures at the recording boundary so callers can keep
their result when the log is unavailable.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.formats.event_lines import encode_line
from wio.log.identify import identify
from wio.log.locate import EVENTS_FILE, locate_log
from wio.models.events import Envelope

if TYPE_CHECKING:
    from pathlib import Path

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
        try:
            if self._disabled():
                return
            path = locate_log(self.repository, self.directories) / EVENTS_FILE
        except Exception as error:  # noqa: BLE001 - recording is best effort
            self._diagnose(error)
            return

        try:
            line = self._line(event)
        except Exception as error:  # noqa: BLE001 - recording is best effort
            self._diagnose(error, path)
            return

        try:
            self.filesystem.append_text(path, line)
        except Exception as error:  # noqa: BLE001 - recording is best effort
            self._diagnose(error, path, appending=True)

    def _line(self, event: Event) -> str:
        """Stamp the event with the current session and encode its line.

        Args:
            event: The event to serialize.

        Returns:
            One encoded event line including its terminating newline.
        """
        identity = identify(self.log, self.environment, self.stdio)
        envelope = Envelope(
            time=self.clock.now(),
            directory=str(self.environment.working_directory()),
            harness=identity.harness,
            session=identity.session,
            parent=identity.parent,
            matches=identity.matches,
            ids=identity.ids,
        )
        return encode_line(envelope, event)

    def _disabled(self) -> bool:
        """Read the log switch before consulting the other ports.

        Returns:
            True when recording is explicitly off.
        """
        return self.environment.get("WIO_LOG") == "off"

    def _diagnose(
        self, _error: Exception, _path: Path | None = None, *, appending: bool = False
    ) -> None:
        """Report a recording failure without affecting the command.

        Args:
            _error: The exception raised by the recording step.
            _path: The events file if location succeeded.
            appending: Whether the failure came from the append port.
        """
