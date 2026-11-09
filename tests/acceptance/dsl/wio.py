# SPDX-License-Identifier: Apache-2.0
"""The `Wio` facade: the verbs a scenario calls, in domain terms."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from tests.acceptance.dsl.results import Output

if TYPE_CHECKING:
    from collections.abc import Sequence

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
            Both output streams and the exit code.
        """
        result = self.driver.run([])
        return Output(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
        )

    def fixture(self, name: str) -> None:
        """Start from a static sample repository.

        Args:
            name: The path of the fixture under `tests/fixtures`, such as
                `config/rich`.
        """
        self.driver.install(name)

    def run(self, args: Sequence[str]) -> Output:
        """Run `wio` with some arguments.

        Args:
            args: The arguments after the program name, such as
                `["config", "show", "works"]`.

        Returns:
            Both output streams and the exit code.
        """
        result = self.driver.run(args)
        return Output(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
        )

    def check_config(self, fixture: str) -> Output:
        """Run `wio config check` on a static sample repository.

        Args:
            fixture: The name of the fixture under `tests/fixtures/config`.

        Returns:
            Both output streams and the exit code.
        """
        self.fixture(f"config/{fixture}")
        return self.run(["config", "check"])
