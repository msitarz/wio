# SPDX-License-Identifier: Apache-2.0
"""The sandbox that keeps a scenario away from the developer's own state."""

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class Sandbox:
    """The directory and environment that a test driver gives `wio`.

    Attributes:
        root: The repository directory `wio` runs in, under `tmp_path`.
        env: The environment `wio` sees; `HOME` and `XDG_DATA_HOME` point
            inside `tmp_path`, so the real log and configuration stay unread.
    """

    root: Path
    env: dict[str, str]

    @classmethod
    def under(cls, tmp_path: Path) -> Sandbox:
        """Create an empty repository directory and a private environment.

        Args:
            tmp_path: The test's own temporary directory.

        Returns:
            A sandbox whose directories exist and lie inside `tmp_path`.
        """
        root = tmp_path / "repo"
        home = tmp_path / "home"
        data = tmp_path / "xdg-data"
        for directory in (root, home, data):
            directory.mkdir()
        env = {**os.environ, "HOME": str(home), "XDG_DATA_HOME": str(data)}
        return cls(root=root, env=env)
