# SPDX-License-Identifier: Apache-2.0
"""The suggestion for a mistyped key, shared by every command that checks keys."""

from typing import TYPE_CHECKING
lazy import difflib

if TYPE_CHECKING:
    from collections.abc import Iterable


def closest_key(key: str, known: Iterable[str]) -> str | None:
    """Find the known key that a mistyped key is closest to.

    It is the one importer of `difflib`, which loads on the first call, not when
    `wio.formats` is imported.

    Args:
        key: The key as written.
        known: The keys that are valid.

    Returns:
        The one known key that `difflib.get_close_matches` ranks first, with its
        default cutoff, or `None` when none is close or there is no known key.
    """
    close = difflib.get_close_matches(key, known, n=1)
    return close[0] if close else None
