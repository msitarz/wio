# SPDX-License-Identifier: Apache-2.0
"""The results a facade verb returns to a scenario."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Output:
    """What a verb that only prints and exits gave back.

    Attributes:
        stdout: What `wio` wrote to standard output.
        stderr: What `wio` wrote to standard error.
        exit_code: The exit code of the run.
    """

    stdout: str
    stderr: str
    exit_code: int
