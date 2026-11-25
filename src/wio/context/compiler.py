# SPDX-License-Identifier: Apache-2.0
"""The compiler: the checks of the inputs and then the composition."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from wio.context import Compiled

if TYPE_CHECKING:
    from wio.context import Check
    from wio.context.ports import Composer


@dataclass(frozen=True)
class Compiler:
    """Checks the inputs of a run and then asks for its bundle.

    Attributes:
        composer: Composes the bundle once every check has passed.
        checks: The checks, in the order they run.
    """

    composer: Composer
    checks: tuple[Check, ...] = ()

    def compile(self, work_id: str, action: str, stage: str) -> Compiled:
        """Run each check in order and then compose the bundle once.

        Args:
            work_id: The Work's id.
            action: The name of the action.
            stage: The name of the stage.

        Returns:
            The bundle with the warnings of the checks, in the order they ran.

        Raises:
            WioError: From the first check that refuses, which stops the run
                before any later check and before the composition, or from the
                composition.
        """
        warnings = tuple(
            text for check in self.checks for text in check(work_id, action, stage)
        )
        return Compiled(self.composer.compose(work_id, action, stage), warnings)
