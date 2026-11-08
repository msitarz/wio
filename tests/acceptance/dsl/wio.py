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
            Both output streams and the exit code.
        """
        result = self.driver.run([])
        return Output(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
        )

    def with_config(self, text: str) -> None:
        """Make the sandbox a repository whose config file holds a text.

        Args:
            text: The content of `.agents/wio/config.toml`.
        """
        self.driver.prepare({".agents/wio/config.toml": text})

    def run_config(self, *args: str) -> Output:
        """Run `wio config` with some arguments.

        Args:
            *args: The arguments after `config`, such as `list` and `--json`.

        Returns:
            Both output streams and the exit code.
        """
        result = self.driver.run(["config", *args])
        return Output(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
        )
