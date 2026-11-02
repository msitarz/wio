# SPDX-License-Identifier: Apache-2.0
"""The ports that two or more components consume identically.

These ports are shared by the components that need them, an exception to the
rule that the consumer owns its ports. A consumer that needs a different view
declares its own port in its `ports.pyi` and does not use these. Provisional:
the members may be narrowed or split once the schemas behind them are decided.
"""

from typing import Protocol

from wio.models.config import Config
from wio.models.events import Event

class Settings(Protocol):
    """The project settings that commands read."""

    def load(self) -> Config:
        """Load the settings.

        Returns:
            The effective settings.

        Raises:
            ValueError: If the settings cannot be read or are inconsistent.
        """
        ...

class EventSink(Protocol):
    """Where events go: the personal event log."""

    def write(self, event: Event) -> None:
        """Append an event to the log.

        A failure to write is reported as a warning and never raised, because
        the log must not block a command.

        Args:
            event: The event to record.
        """
        ...
