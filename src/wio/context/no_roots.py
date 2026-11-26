# SPDX-License-Identifier: Apache-2.0
"""Warn when a stage needs Work roots that are absent."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.context.ports import WorkRoots
    from wio.ports import Settings


@dataclass(frozen=True)
class NoRootsWarning:
    """Check whether a stage selects an empty set of Work roots.

    Attributes:
        settings: Supplies the stage's roots.
        works: Supplies the expanded roots of the Work.
    """

    settings: Settings
    works: WorkRoots

    def __call__(self, work_id: str, action: str, stage: str) -> Sequence[str]:
        """Report a missing set of selected Work roots without refusing the run.

        A stage selects Work roots when its roots are unset or contain `@work`.
        An unknown Work is left to the separate Work check.

        Args:
            work_id: The Work being run.
            action: The action being run.
            stage: A declared stage.

        Returns:
            One warning naming the Work and its lack of roots, or none when its
            roots are not selected, are nonempty, or the Work is unknown.

        Raises:
            ConfigurationError: The settings cannot be loaded.
            KeyError: The stage is not declared.
        """
        del action
        selected = self.settings.load().stages[stage].roots
        if selected is not None and "@work" not in selected:
            return ()
        roots = self.works.roots_of(work_id)
        if roots == ():
            return (f"The Work `{work_id}` has no roots.",)
        return ()
