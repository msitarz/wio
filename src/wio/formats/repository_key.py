# SPDX-License-Identifier: Apache-2.0
"""Stable keys for clone identities shared by logs and bundle files."""

import hashlib
import os
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_DIGEST_LENGTH = 12
_SLUG_LENGTH = 40
_FALLBACK_NAME = "repo"
_GIT_DIRECTORY = ".git"


def _name(identity: Path) -> str:
    """Make the name of a log, for a person, from the identity of its clone.

    Args:
        identity: What `Repository.identity` gives.

    Returns:
        The slug of the last component, or of the one before it when that is
        `.git`, without a trailing `.git`; `repo` when nothing is left.
    """
    component = (
        identity.parent.name if identity.name == _GIT_DIRECTORY else identity.name
    )
    component = component.removesuffix(_GIT_DIRECTORY)
    slug = re.sub(r"[^a-z0-9]+", "-", component.lower())[:_SLUG_LENGTH].strip("-")
    return slug or _FALLBACK_NAME


def repository_key(identity: Path) -> str:
    """Give the human-readable name and digest of a clone identity.

    Args:
        identity: The absolute identity shared by a clone's worktrees.

    Returns:
        The slug and first twelve hexadecimal digits of the identity's SHA-256,
        joined by a hyphen.
    """
    digest = hashlib.sha256(os.fsencode(identity)).hexdigest()[:_DIGEST_LENGTH]
    return f"{_name(identity)}-{digest}"
