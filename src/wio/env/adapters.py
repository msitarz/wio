# SPDX-License-Identifier: Apache-2.0
"""The real adapters of the ports of `wio.env`."""

import os
import secrets
import time
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
        return os.getenv(name)

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
        return time.time()


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
        named = self.environment.get("WIO_HOME")
        if not named:
            return _user_home() / ".agents" / "wio"
        home = Path(named)
        if not home.is_absolute():
            message = f"WIO_HOME must be an absolute path, not {named!r}"
            raise ValueError(message)
        return home


def _user_home() -> Path:
    """Find the user's home directory.

    Returns:
        The absolute home directory of the user.

    Raises:
        OSError: If `Path.home()` cannot find it, or gives a relative path.
    """
    try:
        home = Path.home()
    except RuntimeError as error:
        message = f"cannot find the user's home directory: {error}"
        raise OSError(message) from error
    if not home.is_absolute():
        message = f"the user's home directory is not absolute: {home}"
        raise OSError(message)
    return home
