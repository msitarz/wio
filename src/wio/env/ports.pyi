# SPDX-License-Identifier: Apache-2.0
"""The ports of `wio.env`: what the process knows about its surroundings.

These ports are shared infrastructure that `wio.env` owns, an exception to the
rule that the consumer owns its ports. A component reads the environment
variables, the working directory, the clock, the source of randomness and the
well-known directories only through them, so tests can fix all of them. They
use only standard types, so `wio.env` imports nothing else from `wio`.
Provisional: the members are the ones the data flows of the scope document
need, and the Work that adds an adapter may rename or extend them; other
well-known directories are added by the Work that first needs them.
"""

from pathlib import Path
from typing import Protocol

class Environment(Protocol):
    """Reads the process's environment variables and working directory."""

    def get(self, name: str) -> str | None:
        """Read an environment variable.

        Args:
            name: The variable's name.

        Returns:
            Its value, or `None` when it is not set.
        """
        ...

    def working_directory(self) -> Path:
        """Find the directory the command runs in.

        Returns:
            The absolute working directory.
        """
        ...

class Clock(Protocol):
    """Reads the time, so output that contains times can be tested."""

    def now(self) -> float:
        """Read the clock.

        Returns:
            Seconds since the Unix epoch, in UTC.
        """
        ...

class Entropy(Protocol):
    """Reads random bytes, so generated ids can be tested."""

    def random_bytes(self, count: int) -> bytes:
        """Read cryptographically secure random bytes.

        Args:
            count: How many bytes to return.

        Returns:
            Exactly `count` bytes.
        """
        ...

class Directories(Protocol):
    """Finds the well-known directories that wio writes to, the Wio home included."""

    def temp_dir(self) -> Path:
        """Find the directory for temporary files.

        The result is the directory `$TMPDIR` names, as it is, when `$TMPDIR` is
        set to a non-empty value, without testing it. Otherwise it is `/tmp` on
        Linux or `/private/tmp` on macOS, provided a small test file can be
        written there. An empty `$TMPDIR` counts as unset.

        Returns:
            The directory.

        Raises:
            OSError: If `$TMPDIR` is not set and the system temporary directory
                cannot be written to.
        """
        ...

    def wio_home(self) -> Path:
        """Find the Wio home, where wio keeps its private state for one user.

        The result is the absolute path `$WIO_HOME` names when it is set to a
        non-empty value, and `~/.agents/wio` otherwise, where `~` is the user's
        home directory, which only the adapter of that default reads, and only
        when `$WIO_HOME` is unset. An empty `$WIO_HOME` counts as unset. The
        directory is neither created nor tested, because the first write
        creates it and a failure there is a warning.

        Returns:
            The directory.

        Raises:
            ValueError: If `$WIO_HOME` is set to a relative path.
            OSError: If `$WIO_HOME` is unset and the user's home directory
                cannot be found.
        """
        ...
