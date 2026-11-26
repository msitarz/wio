# SPDX-License-Identifier: Apache-2.0
"""Identify the temporary warning stub at a command boundary."""


class WarningStubReachedError(Exception):
    """A valid command reached the unimplemented warning check."""


def identify_warning_stub(code: int, out: str, err: str) -> None:
    """Identify only the exact exit produced by the temporary warning stub.

    Args:
        code: The command's exit code.
        out: Its standard output.
        err: Its standard error.

    Raises:
        WarningStubReachedError: The stub was reached before writing a bundle.
    """
    if (code, out) == (70, "") and err.endswith(
        "wio.context.no_roots._WarningNotImplementedError\n"
    ):
        raise WarningStubReachedError
