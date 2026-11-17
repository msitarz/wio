# SPDX-License-Identifier: Apache-2.0
"""The ports that `wio.trailers` consumes besides the shared ones in `wio.ports`.

Provisional: the architecture review may rename them. The component that
satisfies each is wired in by `wio.cli`; `wio.trailers` never imports it.
"""

from collections.abc import Mapping, Sequence
from typing import Protocol

from wio.models.events import ContextEvent

class Contracts(Protocol):
    """The Work contracts that a record refers to."""

    def items(self, work_id: str) -> frozenset[str] | None:
        """Find the item ids of a Work.

        The ids are those that the `pattern` directives of the Work's template
        give the Work's own sections, whatever the sections mean; an inherited
        section's ids are not included. The Work is looked up in the working
        tree or in the index, as the adapter was built, and then in `HEAD`,
        which is where a Work that the commit deletes still is.

        Args:
            work_id: The Work's id.

        Returns:
            The Work's item ids, such as `AC-1`, empty for a Work that has
            none, or `None` when no view has such a Work.
        """
        ...

    def pipeline(self, work_id: str, action: str) -> Sequence[str] | None:
        """Find the stages of a Work's action.

        The Work is looked up where `items` looks it up.

        Args:
            work_id: The Work's id.
            action: The name of an action in the config.

        Returns:
            The names of the stages in the order of the pipeline, or `None`
            when the Work or the action does not exist or the Work has no such
            action.
        """
        ...

class Events(Protocol):
    """The event log, read back."""

    def first_context(
        self, work_id: str, action: str, stage: str
    ) -> ContextEvent | None:
        """Find where a session's review of a stage started.

        Args:
            work_id: The Work's id.
            action: The action.
            stage: The stage, which is a gate.

        Returns:
            The first `context` event of this session for the gate, or the
            earliest one from the same working directory since the latest
            `review` event when the session id is unknown; `None` when there is
            none.
        """
        ...

class StageRules(Protocol):
    """The rules that a stage selects for a Work."""

    def selected(self, work_id: str, action: str, stage: str) -> Mapping[str, str]:
        """Find the rules that a stage selects for a Work.

        The component that selects the rules satisfies it; until it exists,
        `wio trailers` wires an adapter that selects none, so a cited rule code is
        refused.

        Args:
            work_id: The Work's id.
            action: The action.
            stage: The stage.

        Returns:
            The qualified code of each rule the stage selects, such as
            `docs.DOC001`, with the hash of the rule's file that the `context`
            event records, and empty when the stage selects none.
        """
        ...
