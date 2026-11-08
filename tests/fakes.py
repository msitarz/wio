# SPDX-License-Identifier: Apache-2.0
"""Fakes that tests of more than one group share."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class FakeEnvironment:
    """An `Environment` with a fixed working directory and the given variables."""

    directory: Path
    variables: dict[str, str] = field(default_factory=dict)

    def get(self, name: str) -> str | None:
        """Read a variable of the fake.

        Args:
            name: The variable's name.

        Returns:
            Its value, or None when the fake has no such variable.
        """
        return self.variables.get(name)

    def working_directory(self) -> Path:
        """Find the fixed working directory.

        Returns:
            The directory the fake was given.
        """
        return self.directory
