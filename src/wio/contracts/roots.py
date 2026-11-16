# SPDX-License-Identifier: Apache-2.0
"""The special entry and validity rule for a Work's roots."""

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Collection

DESCENDANTS: Final = "@descendants"
"""The entry that resolves to the roots of a Work's descendants."""


def undeclared_root(name: str, declared: Collection[str]) -> bool:
    """Say whether a Work's root entry is neither special nor declared.

    Args:
        name: A root entry from a Work or a creation request.
        declared: The root names declared in the config.

    Returns:
        Whether the entry names an undeclared root.
    """
    return name != DESCENDANTS and name not in declared
