# SPDX-License-Identifier: Apache-2.0
"""The null adapters that `wio.cli` wires where a component is missing.

`wio trailers` consumes the rules of a stage and an event sink, and neither
component exists yet. Until the rules component satisfies `StageRules`, the command
wires a port that selects no rule, so a cited rule code is refused as not selected,
and until `wio log` exists it wires a sink that drops every event, as constraint C-4
of the top parent says, so a recorded gate result leaves nothing in the Wio home.
They live in `wio.cli`, the one place that builds adapters, and `wio.trailers` never
imports them.
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
