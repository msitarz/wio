# SPDX-License-Identifier: Apache-2.0
"""The null adapters available at the command composition boundary.

Tests can inject `NoEvents` when a review should have no side effects.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.models.events import Event


class NoEvents:
    """An `EventSink` that drops every event."""

    def write(self, event: Event) -> None:
        """Drop the event.

        It reads nothing, writes nothing and raises nothing, so no file appears in
        the Wio home.

        Args:
            event: The event, which is ignored.
        """
        del event
