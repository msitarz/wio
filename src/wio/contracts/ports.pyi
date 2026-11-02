# SPDX-License-Identifier: Apache-2.0
"""The ports that `wio.contracts` consumes.

Provisional: the architecture review may rename them. The component that
satisfies each is wired in by `wio.cli`; `wio.contracts` never imports it.
"""

from typing import Protocol

from wio.models.config import Config

class Settings(Protocol):
    """The project settings that contract commands read."""

    def load(self) -> Config:
        """Load the settings.

        Returns:
            The effective settings.

        Raises:
            ValueError: If the settings cannot be read or are inconsistent.
        """
        ...
