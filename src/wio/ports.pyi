# SPDX-License-Identifier: Apache-2.0
"""The ports that two or more components consume identically.

A port is declared here when two or more components need it with the same
members and the same signatures, an exception to the rule that the consumer owns
its ports. The components and `wio.cli` may import this stub; `wio.io`,
`wio.env` and `wio.models` never do. A consumer that needs a different view
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
            ConfigurationError: If the settings cannot be read or are
                inconsistent.
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
