# SPDX-License-Identifier: Apache-2.0
"""The ports that `wio.trailers` consumes.

Provisional: the architecture review may rename them. The component that
satisfies each is wired in by `wio.cli`; `wio.trailers` never imports it.
"""

from typing import Protocol

from wio.models.config import Config
from wio.models.events import Event

class Settings(Protocol):
    """The project settings that trailer commands read."""

    def load(self) -> Config:
        """Load the settings.

        Returns:
            The effective settings.

        Raises:
            ValueError: If the settings cannot be read or are inconsistent.
        """
        ...

class Contracts(Protocol):
    """The Work contracts that a record refers to."""

    def criteria(self, work_id: str) -> frozenset[str] | None:
        """Find the acceptance criteria of a Work.

        Args:
            work_id: The Work's id.

        Returns:
            The ids of the Work's criteria, such as `AC-1`, or `None` when no
            such Work exists in the working tree or in `HEAD`.
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
