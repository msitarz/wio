# SPDX-License-Identifier: Apache-2.0
"""The real adapters of the ports of `wio.env`."""

import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wio.env.ports import Environment


class ProcessEnvironment:
    """The process's own surroundings, as the `Environment` port.

    The one place of `src/wio` that reads the variables of the process and its
    working directory, so a component gets them only through the port.
    """

    def get(self, name: str) -> str | None:
        """Read an environment variable as it is at the time of the call.

        Args:
            name: The variable's name.

        Returns:
            Its value, `None` when it is not set, and `""` when it is set to an
            empty string, which the caller decides how to read.
        """
        raise NotImplementedError

    def working_directory(self) -> Path:
        """Find the directory the process runs in.

        Returns:
            The absolute working directory of the process, the one place of
            `src/wio` that reads it.
        """
        return Path.cwd()


class SystemEntropy:
    """The operating system's source of randomness, as the `Entropy` port."""

    def random_bytes(self, count: int) -> bytes:
        """Read cryptographically secure random bytes.

        Args:
            count: How many bytes to return.

        Returns:
            Exactly `count` bytes from the operating system.
        """
        return secrets.token_bytes(count)


class SystemClock:
    """The system's clock, as the `Clock` port.

    The names of this class and of `ProcessDirectories` are provisional.
    """

    def now(self) -> float:
        """Read the clock.

        Returns:
            Seconds since the Unix epoch, in UTC, as `time.time()` gives them.
        """
        raise NotImplementedError


@dataclass(frozen=True)
class ProcessDirectories:
    """The well-known directories of the process's user, as the `Directories` port.

    Attributes:
        environment: Where `WIO_HOME` is read, so a test can fix it.
    """

    environment: Environment

    def temp_dir(self) -> Path:
        """Find the directory for temporary files.

        Raises:
            NotImplementedError: Always, naming `temp_dir`, until the Work that
                first needs it gives it its meaning.
        """
        message = "temp_dir is implemented by the Work that first needs it"
        raise NotImplementedError(message)

    def wio_home(self) -> Path:
        """Find the Wio home by the rule of `Directories.wio_home`.

        Nothing is created or tested. The environment is read at each call, and
        `Path.home()` only when `WIO_HOME` is unset or empty.

        Returns:
            The absolute path `WIO_HOME` names, or `.agents/wio` under the
            user's home directory.

        Raises:
            ValueError: If `WIO_HOME` is a relative path; the message names
                `WIO_HOME` and says `absolute`.
            OSError: If the user's home directory cannot be found or is not
                absolute.
        """
        raise NotImplementedError
