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

    def put(self, path: str, data: bytes) -> None:
        """Write a file into the repository of the scenario.

        Args:
            path: The file, relative to the root of the repository.
            data: Its bytes.
        """
        self.driver.put(path, data)

    def fingerprint(self, directory: str) -> dict[str, str]:
        """Fingerprint the files below a directory of the repository.

        Args:
            directory: The directory, relative to the root of the repository.

        Returns:
            The SHA-256 of each file by its path relative to the directory.
        """
        return self.driver.fingerprint(directory)

    def read(self, path: str) -> bytes:
        """Read a file of the scenario's repository.

        Args:
            path: The file relative to the root.

        Returns:
            The file's bytes.
        """
        return self.driver.read(path)

    def run(
        self, args: Sequence[str], directory: str | None = None, stdin: str = ""
    ) -> Output:
        """Run `wio` with some arguments.

        Args:
            args: The arguments after the program name, such as
                `["config", "show", "works"]`.
            directory: A directory below the root of the repository to run in,
                or `None` to run at the root.
            stdin: What standard input holds.

        Returns:
            Both output streams and the exit code.
        """
        result = self.driver.run(args, directory, stdin)
        return Output(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
        )

    def commit(self, message: str, *, empty: bool = False) -> None:
        """Stage everything and commit it, as the fixed identity of the sandbox.

        Only the CLI channel has a git repository.

        Args:
            message: The whole commit message.
            empty: Whether to allow a commit that changes nothing, as a gate's own
                commit does.

        Raises:
            AssertionError: If git refused the commit.
        """
        self.driver.git(["add", "-A"])
        flags = ["--allow-empty"] if empty else []
        done = self.driver.git(["commit", "--quiet", *flags, "-m", message])
        assert done.exit_code == 0, done.stderr

    def check_config(self, fixture: str) -> Output:
        """Run `wio config check` on a static sample repository.

        Args:
            fixture: The name of the fixture under `tests/fixtures/config`.

        Returns:
            Both output streams and the exit code.
        """
        self.fixture(f"config/{fixture}")
        return self.run(["config", "check"])
