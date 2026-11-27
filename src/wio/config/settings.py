# SPDX-License-Identifier: Apache-2.0
"""The adapter of the `Settings` port of `wio.ports`."""

from typing import TYPE_CHECKING

from wio.config.checks import CHECKS
from wio.config.loader import config_or_raise, load_config

if TYPE_CHECKING:
    from collections.abc import Sequence

    from wio.config.checks import Check
    from wio.io.ports import FileSystem, Repository
    from wio.models.config import Config


class ConfigSettings:
    """The settings of the project, read through the loader, as `Settings`."""

    def __init__(
        self,
        repository: Repository,
        files: FileSystem,
        checks: Sequence[Check] = CHECKS,
    ) -> None:
        """Keep the ports and the checks that `load` hands to the loader.

        Args:
            repository: The port that finds the repository's root.
            files: The port that reads the config file.
            checks: What runs after the shape, in order; `CHECKS` by default.
        """
        self._repository = repository
        self._files = files
        self._checks = checks
        self._cached: Config | None = None

    def load(self) -> Config:
        """Load the settings once and cache the result, or refuse with every error.

        Returns:
            The `Config`, when no diagnostic of the check run is an error;
            warnings and notes never block.

        Raises:
            ConfigurationError: A diagnostic is an error, or the file cannot be
                found or read. It carries every error and its message renders
                them.
        """
        if self._cached is None:
            self._cached = config_or_raise(
                load_config(self._repository, self._files, self._checks)
            )
        return self._cached
