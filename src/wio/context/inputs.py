# SPDX-License-Identifier: Apache-2.0
"""Refuse names that cannot identify the requested context."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.context.ports import WorkRoots
    from wio.ports import Settings


@dataclass(frozen=True)
class KnownInputs:
    """Check the names of an action, stage and selected Work roots.

    Attributes:
        settings: Supplies the declared names and stage roots.
        works: Supplies expanded Work roots.
    """

    settings: Settings
    works: WorkRoots

    def __call__(self, work_id: str, action: str, stage: str) -> Sequence[str]:
        """Refuse unknown names before composition.

        A stage selects Work roots when its roots are unset or include `@work`.
        Other stages do not look up the Work's roots. An unknown Work is left
        to the separate Work check.

        Args:
            work_id: The Work being run.
            action: The requested action.
            stage: The requested stage.

        Returns:
            No warnings when all selected names are known.

        Raises:
            WioError: An action, stage or selected Work root is unknown.
            ConfigurationError: The settings cannot be loaded.
        """
        raise NotImplementedError
