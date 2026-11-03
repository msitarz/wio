# SPDX-License-Identifier: Apache-2.0
"""The test driver Protocol: how a scenario's facade reaches `wio`."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class RunResult:
    """What one run of `wio` produced, as plain data.

    Attributes:
        stdout: Everything written to standard output.
        stderr: Everything written to standard error.
        exit_code: The exit code of the run.
    """

    stdout: str
    stderr: str
    exit_code: int


class WioDriver(Protocol):
    """A test driver: runs `wio` on one channel and returns data.

    An implementation never asserts, so every channel gives a scenario the same
    kind of value.
    """

    def run(self, args: Sequence[str]) -> RunResult:
        """Run `wio` with the given arguments in the driver's sandbox.

        Args:
            args: The arguments after the program name.

        Returns:
            The streams and exit code of the run.
        """
        ...
