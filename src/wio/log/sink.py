# SPDX-License-Identifier: Apache-2.0
"""Stamp events and append them to the log shared by a clone's worktrees.

The sink contains failures at the recording boundary so callers can keep
their result when the log is unavailable.
"""

from contextlib import suppress
from dataclasses import dataclass
from errno import EROFS
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


_SWITCH_WARNING = (
    'warning: WIO_LOG must be "off" to switch the log off; the log stays on'
)
_HOME_HINT = (
    "hint: add an exception to your harness's configuration for ~/.agents/wio "
    "or set $WIO_HOME to a directory your harness allows"
)


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
        switch = self.environment.get("WIO_LOG")
        if switch == "off":
            return True
        if switch:
            with suppress(Exception):
                self.stdio.stderr.write(_SWITCH_WARNING + "\n")
        return False

    def _diagnose(
        self, error: Exception, path: Path | None = None, *, appending: bool = False
    ) -> None:
        """Report a recording failure without affecting the command.

        Args:
            error: The exception raised by the recording step.
            path: The events file if location succeeded.
            appending: Whether the failure came from the append port.
        """
        message = _message(error)
        with suppress(Exception):
            if path is None:
                self.stdio.stderr.write(
                    f"warning: the event log could not be located: {message}\n"
                )
                return
            self.stdio.stderr.write(
                f"warning: the event log could not be written: {path}: {message}\n"
            )
            if (
                appending
                and _permission_failure(error)
                and not self.environment.get("WIO_HOME")
            ):
                self.stdio.stderr.write(_HOME_HINT + "\n")


def _message(error: Exception) -> str:
    """Give the failure message on a single line.

    Args:
        error: The recording failure, possibly with a system error message.

    Returns:
        The system message when available, the exception text otherwise, or
        the exception class name when no usable message is available.
    """
    with suppress(Exception):
        system_message = error.strerror if isinstance(error, OSError) else None
        text = system_message or str(error)
        if text:
            return text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    return type(error).__name__


def _permission_failure(error: Exception) -> bool:
    """Tell whether an append failure suggests an unwritable Wio home.

    Args:
        error: The failure raised by the append.

    Returns:
        True for permission denied or a read-only filesystem.
    """
    return isinstance(error, PermissionError) or (
        isinstance(error, OSError) and error.errno == EROFS
    )
