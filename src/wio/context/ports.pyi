# SPDX-License-Identifier: Apache-2.0
"""The ports that `wio.context` consumes besides the shared ones in `wio.ports`.

Provisional: the architecture review may rename them. The component that
satisfies each is wired in by `wio.cli`; `wio.context` never imports it.
"""

from typing import Protocol

from wio.models.rules import Selection
from wio.models.work import ResolvedContract

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

    def select(self, contract: ResolvedContract, stage: str) -> Selection:
        """Select the rules for a stage of a Work.

        Args:
            contract: The Work's resolved contract, which gives its roots.
            stage: The name of a stage in the config.

        Returns:
            Every rule considered, in a fixed order so the same inputs give the
            same bytes, each with its decision: the roots of an included rule,
            or why a rule was left out.

        Raises:
            KeyError: If the stage is not in the config.
            ValueError: If the stage selects the Work's roots and the Work has
                none.
        """
        ...
