# SPDX-License-Identifier: Apache-2.0
"""Path resolution shared by the local filesystem and read-only views."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


class PathResolution:
    """Resolve local paths for adapters that expose the filesystem port."""

    def resolve(self, path: Path) -> Path:
        """Resolve a path, following links even when the destination is missing.

        Args:
            path: A path absolute or relative to the working directory.

        Returns:
            The absolute path with symbolic links followed.
        """
        return path.resolve()
