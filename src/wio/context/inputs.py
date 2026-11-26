# SPDX-License-Identifier: Apache-2.0
"""Refuse names that cannot identify the requested context."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.errors import WioError

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from wio.context.ports import WorkRoots
    from wio.models.config import Config
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
        config = self.settings.load()
        _known("action", action, config.actions)
        _known("stage", stage, config.stages)
        selected = config.stages[stage].roots
        if selected is None or "@work" in selected:
            _known_roots(work_id, self.works, config)
        return ()


def _known_roots(work_id: str, works: WorkRoots, config: Config) -> None:
    """Refuse an undeclared root selected from a Work.

    Args:
        work_id: The Work whose roots are selected.
        works: Supplies the expanded roots.
        config: Declares the roots.

    Raises:
        WioError: A Work root is unknown.
    """
    for root in works.roots_of(work_id) or ():
        if root not in config.roots:
            message = f"The Work `{work_id}` names unknown root `{root}`."
            raise WioError(message)


def _known(kind: str, name: str, declared: Mapping[str, object]) -> None:
    """Refuse an unknown name and list the declared names.

    Args:
        kind: The kind of name for the message.
        name: The requested name.
        declared: The declared names.

    Raises:
        WioError: The name is not declared.
    """
    if name not in declared:
        names = ", ".join(f"`{item}`" for item in sorted(declared)) or "none"
        message = f"Unknown {kind} `{name}`. Declared {kind}s: {names}."
        raise WioError(message)
