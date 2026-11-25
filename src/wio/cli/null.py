# SPDX-License-Identifier: Apache-2.0
"""The null adapters available at the command composition boundary.

Tests can inject `NoEvents` when a review should have no side effects, and
`UnwiredComposer` stands where `wio context` has no composition yet.
"""

from typing import TYPE_CHECKING

from wio.errors import WioError

if TYPE_CHECKING:
    from wio.models.bundle import CompiledBundle
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


class UnwiredComposer:
    """A `Composer` that refuses, until the composition of the bundle is wired."""

    def compose(self, work_id: str, action: str, stage: str) -> CompiledBundle:
        """Refuse to compose.

        It reads nothing and writes nothing.

        Args:
            work_id: The Work's id, which is ignored.
            action: The action, which is ignored.
            stage: The stage, which is ignored.

        Raises:
            WioError: Always, saying that the bundle cannot be composed yet, so a
                run exits 2 and is not taken for a bug.
        """
        del work_id, action, stage
        message = "wio context cannot compose a bundle yet"
        raise WioError(message)
