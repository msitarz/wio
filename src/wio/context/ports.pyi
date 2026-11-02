# SPDX-License-Identifier: Apache-2.0
"""The ports that `wio.context` consumes.

Provisional: the architecture review may rename them. The component that
satisfies each is wired in by `wio.cli`; `wio.context` never imports it.
"""

from collections.abc import Sequence
from typing import Protocol

from wio.models.config import Config
from wio.models.events import Event
from wio.models.rules import Rule
from wio.models.work import ResolvedContract

class Settings(Protocol):
    """The project settings that context commands read."""

    def load(self) -> Config:
        """Load the settings.

        Returns:
            The effective settings.

        Raises:
            ValueError: If the settings cannot be read or are inconsistent.
        """
        ...

class Contracts(Protocol):
    """The Work contracts that a bundle shows."""

    def resolved(self, work_id: str) -> ResolvedContract:
        """Read a Work's contract with its ancestors' inherited sections.

        Args:
            work_id: The Work's id.

        Returns:
            The resolved contract.

        Raises:
            KeyError: If no Work has that id.
        """
        ...

class RuleSelection(Protocol):
    """The rules that apply to a Work at a stage."""

    def select(self, contract: ResolvedContract, stage: str) -> Sequence[Rule]:
        """Select the rules for a stage of a Work.

        Args:
            contract: The Work's resolved contract, which gives its roots and
                its template's type.
            stage: The name of a stage in the config.

        Returns:
            The rules in a fixed order, so the same inputs give the same bytes.

        Raises:
            KeyError: If the stage is not in the config.
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
