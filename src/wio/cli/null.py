# SPDX-License-Identifier: Apache-2.0
"""The null adapters available at the command composition boundary.

`wio trailers` wires `NoRules` until a component supplies the rules of a
stage. Tests can inject `NoEvents` when a review should have no side effects.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from wio.models.events import Event


class NoRules:
    """A `StageRules` port that selects no rule for any stage."""

    def selected(self, work_id: str, action: str, stage: str) -> Mapping[str, str]:
        """Select no rule.

        Args:
            work_id: The Work's id, which is ignored.
            action: The action, which is ignored.
            stage: The stage, which is ignored.

        Returns:
            An empty mapping, so no rule code is selected.
        """
        del work_id, action, stage
        return {}


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
