# SPDX-License-Identifier: Apache-2.0
"""The real adapters of the ports of `wio.io`."""

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TextIO


class SystemStdio:
    """The process's own standard streams, as the `Stdio` port.

    Once built, its `stdin`, `stdout` and `stderr` are the streams of `sys`.
    """

    stdin: TextIO
    stdout: TextIO
    stderr: TextIO

    def __init__(self) -> None:
        """Bind the streams of `sys`."""
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr
