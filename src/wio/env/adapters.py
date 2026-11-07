# SPDX-License-Identifier: Apache-2.0
"""The real adapters of the ports of `wio.env`."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class ProcessEnvironment:
    """The process's own surroundings, as the `Environment` port.

    Only `working_directory` is implemented, because the repository adapter is
    the first to need the environment. The other members exist so that the class
    can be wired where the port is expected, and raise `NotImplementedError`
    until the Work that first needs them gives them their meaning.
    """

    def get(self, name: str) -> str | None:
        """Read an environment variable.

        Args:
            name: The variable's name.

        Raises:
            NotImplementedError: Always, until the Work that first needs it
                implements it.
        """
        message = "get is implemented by the Work that first needs it"
        raise NotImplementedError(message)

    def working_directory(self) -> Path:
        """Find the directory the process runs in.

        Returns:
            The absolute working directory of the process.
        """
        raise NotImplementedError
