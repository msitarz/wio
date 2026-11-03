# SPDX-License-Identifier: Apache-2.0
"""The sandbox that keeps a scenario away from the developer's own state."""

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

# Git sets these for a hook, and they would aim a scenario's git at the
# developer's own repository, index or objects, or add config from outside.
_GIT_REDIRECTS = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
        "GIT_PREFIX",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_SYSTEM",
        "WIO_HOME",
    }
)

# An empty global config that also stops git reading the developer's global
# ignore and attributes files, which its defaults would find under `~/.config`.
_GITCONFIG = "[core]\n\texcludesFile = /dev/null\n\tattributesFile = /dev/null\n"

_IDENTITY = {
    "NAME": "Wio Test",
    "EMAIL": "wio-test@example.invalid",
    "DATE": "2026-01-01T00:00:00+0000",
}


def _inherited() -> dict[str, str]:
    """Copy the process environment without what would leak the developer's.

    Returns:
        The variables left after the ones that redirect git, set a Wio home or
        make git trace to standard error are dropped.
    """
    return {
        key: value
        for key, value in os.environ.items()
        if key not in _GIT_REDIRECTS and not key.startswith("GIT_TRACE")
    }


@dataclass(frozen=True)
class Sandbox:
    """The directory and environment that a test driver gives `wio`.

    Attributes:
        root: The repository directory `wio` runs in, under `tmp_path`.
        env: The environment `wio` sees. `WIO_HOME` is under `tmp_path`, so the
            real Wio home stays unread, and `HOME` is left alone because `wio`
            reads it only when `WIO_HOME` is unset. Git reads no global or
            system config, finds no repository above `tmp_path`, is not aimed
            at another one, and commits as a fixed identity.
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
        root.mkdir(parents=True)
        gitconfig = tmp_path / "gitconfig"
        gitconfig.write_text(_GITCONFIG, encoding="utf-8")
        env = {
            **_inherited(),
            "WIO_HOME": str(tmp_path / "wio-home"),
            "GIT_CONFIG_GLOBAL": str(gitconfig),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CEILING_DIRECTORIES": str(tmp_path.resolve()),
        }
        for role in ("AUTHOR", "COMMITTER"):
            env |= {f"GIT_{role}_{key}": value for key, value in _IDENTITY.items()}
        return cls(root=root, env=env)
