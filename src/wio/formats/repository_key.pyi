# SPDX-License-Identifier: Apache-2.0
"""The stable, human-readable key of a clone's repository identity."""

from pathlib import Path

def repository_key(identity: Path) -> str:
    """Name a clone from its identity with the log directory's key rule.

    Args:
        identity: The absolute identity shared by the clone's worktrees.

    Returns:
        The existing log directory's name and digest, joined by a hyphen.
    """
    ...
