# SPDX-License-Identifier: Apache-2.0
"""Identify the temporary pipeline warning stub at the command boundary."""


class PipelineStubReachedError(Exception):
    """A valid command reached the unimplemented pipeline warning."""


def identify_pipeline_stub(code: int, out: str, err: str) -> None:
    """Identify only the exit produced by the temporary warning stub.

    Args:
        code: The command's exit code.
        out: Its standard output.
        err: Its standard error.

    Raises:
        PipelineStubReachedError: The stub was reached before writing a bundle.
    """
    if (code, out) == (70, "") and err.endswith(
        "wio.context.pipeline._PipelineNotImplementedError\n"
    ):
        raise PipelineStubReachedError
