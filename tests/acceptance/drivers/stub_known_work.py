# SPDX-License-Identifier: Apache-2.0
"""Identify the temporary Work check stub at the command boundary."""


class KnownWorkStubReachedError(Exception):
    """A command reached the unimplemented Work check."""


def identify_known_work_stub(code: int, out: str, err: str) -> None:
    """Identify only the exit produced by the temporary stub.

    Args:
        code: The command's exit code.
        out: Its standard output.
        err: Its standard error.

    Raises:
        KnownWorkStubReachedError: The stub was reached before writing a bundle.
    """
    if (code, out) == (70, "") and err.endswith(
        "wio.context.known_work._KnownWorkNotImplementedError\n"
    ):
        raise KnownWorkStubReachedError
