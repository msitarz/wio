# SPDX-License-Identifier: Apache-2.0
"""The `Wio` facade: the verbs a scenario calls, in domain terms."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tests.acceptance.dsl.results import Output

if TYPE_CHECKING:
    from tests.acceptance.drivers.base import WioDriver


@dataclass(frozen=True)
class Wio:
    """What a scenario sees of `wio`, whatever channel reaches it.

    Operation-shaped verbs are layered on the test driver's `run(args)` as
    scenarios need them.

    Attributes:
        driver: The test driver of the scenario's channel.
    """

    driver: WioDriver

    def bare(self) -> Output:
        """Run `wio` with no arguments.

        Returns:
            The text on standard output and the exit code.
        """
        result = self.driver.run([])
        return Output(text=result.stdout, exit_code=result.exit_code)
